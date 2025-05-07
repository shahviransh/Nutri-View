import sqlite3
import os
import pandas as pd
import numpy as np
from PIL import Image
import geopandas as gpd
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import cmocean.cm
import itertools
from sklearn.preprocessing import KBinsDiscretizer
from scipy.stats import skew
from matplotlib.ticker import MaxNLocator, LinearLocator
from cycler import cycler
from config import Config
from datetime import datetime
import sys
import json
from concurrent.futures import ThreadPoolExecutor
import pyogrio
from osgeo import ogr, osr, gdal
from zipfile import ZipFile, ZIP_DEFLATED
from werkzeug.utils import safe_join
import re
import numexpr as ne

alias_mapping = {}
global_dbs_tables_columns = {}
os.environ["PROJ_LIB"] = Config.PROJ_LIB
os.environ["GDAL_DATA"] = Config.GDAL_DATA
bmp_db_path_global = None
os.makedirs(Config.TEMPDIR, exist_ok=True)


def fetch_data_service(data):
    """Fetch data and statistics from the specified databases and tables."""
    try:
        # Extract the required parameters from the request data
        db_tables = json.loads(data.get("db_tables"))
        columns = (
            json.loads(data.get("columns")) if data.get("columns") != "All" else "All"
        )
        selected_ids = json.loads(data.get("id"))
        id_column = data.get("id_column", "ID")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        date_type = data.get("date_type")
        interval = data.get("interval", "daily")
        method = json.loads(data.get("method", "['Equal']"))
        statistics = json.loads(data.get("statistics", "['None']"))
        month = data.get("month", None)
        season = data.get("season", None)
        spatial_scale = data.get("spatial_scale", None)
        field_selected_ids = data.get("field_selected_ids", [])
        math_formula = data.get("math_formula", None)
        stats_df = None

        if spatial_scale == "field":
            field_selected_ids = selected_ids
            selected_ids = []

        # Initialize DataFrame to store the merged data
        df = pd.DataFrame()

        # Fetch the data for each database and table, and merge it based on date_type & 'ID'
        for table in db_tables:
            try:
                table_key = f"{(table['db'], table['table'])}"
                global_columns = global_dbs_tables_columns.get(table_key)
                ID = (
                    [id_column]
                    if global_columns and id_column in global_columns
                    else []
                )
                duplicate_columns = []
                is_all_columns = False

                if not global_columns:
                    return {"error": f"No columns found for the table {table_key}"}

                # Determine which columns to fetch
                if columns == "All":
                    # Fetch all columns for the table
                    fetch_columns = columns
                    is_all_columns = True
                else:
                    fetch_columns = set()
                    prefix_columns = [
                        col for col in columns if col.startswith(table["table"])
                    ]

                    # Check if the table has a prefix
                    for col in columns:
                        if col in prefix_columns:
                            original_col = col[
                                len(table["table"]) + 1 :
                            ]  # Strip prefix
                            if original_col in global_columns:
                                fetch_columns.add(original_col)
                                duplicate_columns.append(col)
                        elif col in global_columns:
                            # Non-prefixed columns for tables without prefixes
                            fetch_columns.add(col)

                # Remove fetched columns from columns list
                columns = list(set(columns) - set(fetch_columns)) + [date_type] + ID

                if not fetch_columns:
                    # If there are no common columns, skip the table
                    continue

                # Fetch data from the database
                df_temp = fetch_data_from_db(
                    table["db"],
                    table["table"],
                    selected_ids,
                    fetch_columns,
                    start_date,
                    end_date,
                    date_type,
                )

                # Rename columns to table-column format
                for col in duplicate_columns:
                    col_temp = col[len(table["table"]) + 1 :]
                    if col_temp in df_temp.columns:
                        df_temp.rename(columns={col_temp: col}, inplace=True)

                # Merge the dataframes on date_type and 'ID' columns
                if df.empty:
                    df = df_temp
                else:
                    # Case of All columns, rename columns to table-column format
                    if is_all_columns:
                        for col in df.columns:
                            if col in df_temp.columns:
                                df_temp.rename(
                                    columns={col: f"{table['table']}-{col}"},
                                    inplace=True,
                                )

                    # Identify columns for merging; ignore columns with dash if they represent different data sources
                    merge_on_columns = [
                        col for col in df.columns if "ID" in col
                    ]
                    for col in df.columns:
                        if col in df_temp.columns and not col.startswith(
                            table["table"]
                        ):
                            merge_on_columns.append(col)
                    df = pd.merge(df, df_temp, on=merge_on_columns, how="inner")
                    # Drop rows with NaN in the required columns
                    df.dropna(inplace=True)
            except Exception as e:
                return {"error": f"Error while processing table {table_key}: {str(e)}"}

        # If the DataFrame is empty after merging, return an error
        if df.empty:
            return {"error": "No data found for the specified filters."}

        ID = id_column

        if spatial_scale == "field":
            # Connect to BMP.db3 to fetch subarea information
            bmp_db_path = safe_join(Config.PATHFILE, bmp_db_path_global)
            conn = sqlite3.connect(bmp_db_path)

            try:
                # Get the ID column name for Subarea table
                query = f"PRAGMA table_info('Subarea')"
                cursor = conn.cursor()
                cursor.execute(query)
                subarea_id = next(
                    (col[1] for col in cursor.fetchall() if "id" in col[1].lower()),
                    "ID",
                )

                # Read Subarea information (Id, FieldId, and Area) from the Subarea table
                query = f"SELECT {subarea_id} AS '{ID}', FieldId, Area FROM Subarea"
                params = []

                # Add conditions for selected field IDs
                if field_selected_ids:
                    placeholders = ",".join(["?"] * len(field_selected_ids))
                    query += f" WHERE FieldId IN ({placeholders})"
                    params.extend(field_selected_ids)
                subarea_df = pd.read_sql_query(query, conn, params=params)

                # Ensure the required columns exist in the DataFrame
                if (
                    ID not in subarea_df.columns
                    or "FieldId" not in subarea_df.columns
                    or "Area" not in subarea_df.columns
                ):
                    return {
                        "error": "Subarea table does not contain the required columns: ID, FieldId, Area"
                    }

                # Calculate the total area for each field
                field_area_df = (
                    subarea_df.groupby(["FieldId"])["Area"].sum().reset_index()
                )
                field_area_df.rename(columns={"Area": "Total_Area"}, inplace=True)

                # Merge the total field area back into the subarea DataFrame
                subarea_df = subarea_df.merge(field_area_df, on="FieldId")

                # Calculate the area fraction for each subarea within its field
                subarea_df["Area_Fraction"] = (
                    subarea_df["Area"] / subarea_df["Total_Area"]
                )

                date_type_list = [date_type] if date_type else []

                # Merge the subarea values from the main DataFrame (df) into the subarea DataFrame
                subarea_values = (
                    df.set_index([ID, *date_type_list])
                    .select_dtypes(include=["number"])
                    .reset_index()
                )
                subarea_values.rename(columns={ID: "Subarea_ID"}, inplace=True)
                subarea_df = subarea_df.merge(
                    subarea_values, left_on=ID, right_on="Subarea_ID", how="left"
                )

                # Calculate the area-weighted field values for all numerical columns
                weighted_columns = []
                for col in subarea_values.columns:
                    if col not in [
                        "Subarea_ID",
                        *date_type_list,
                    ]:  # Skip the ID and Date column
                        subarea_df[col] = subarea_df[col] * subarea_df["Area_Fraction"]
                        weighted_columns.append(col)

                # Aggregate the weighted values to calculate the field values
                field_values_df = (
                    subarea_df.groupby(["FieldId", *date_type_list])[weighted_columns]
                    .sum()
                    .reset_index()
                )
                field_values_df.rename(columns={"FieldId": ID}, inplace=True)

                # Replace the original DataFrame's values with the calculated field values
                df = field_values_df.copy().map(round_numeric_values)

            except Exception as e:
                return {"error": f"Error processing field values: {str(e)}"}
            finally:
                conn.close()
        elif spatial_scale == "reach":
            # Select all IDs except 0 as Reach ID = 0 is used for watershed average
            df = df[df[ID] != 0]
        elif spatial_scale == "unknown":
            return {
                "error": "Spatial scale is unknown. Please select a valid spatial scale."
            }

        # Combine all numerical columns in df.columns except 'ID' using the specified math_sign
        numerical_columns = [
            col for col in df.select_dtypes(include=["number"]).columns if col != ID
        ]
        new_feature = ""

        # Parse and evaluate the formula dynamically
        if math_formula:
            try:
                # Replace column names in the formula with their corresponding DataFrame references
                formula = math_formula
                formula_symbols = math_formula
                for col in numerical_columns:
                    formula = formula.replace(col, f"df['{col}']", 1)
                    # Remove column names from the formula symbols
                    formula_symbols = formula_symbols.replace(col, "", 1)

                # Check if formula only contains allowed mathematical operators and column names
                formula_symbols = set(list(formula_symbols))

                if not all(
                    char.isnumeric() or char in "+-*/,." or char.isspace()
                    for char in formula_symbols
                ):
                    return {"error": "Invalid characters or columns in the formula."}

                # Create a mapping of alias to real column names
                real_col = {
                    col: columns_dict[col]
                    for table in db_tables
                    for col in numerical_columns
                    if col
                    in (
                        columns_dict := alias_mapping.get(table["table"], {}).get(
                            "columns", {}
                        )
                    )
                }

                special_chars = "!@#$%^&()_+-*/.|~/`{}[]:;\"\\'<>,?0123456789 "

                # Replace only column names in the formula, ignoring operators
                new_feature = math_formula
                for col in numerical_columns:
                    if col in real_col:
                        new_feature = new_feature.replace(col, real_col.get(col, col))
                    math_formula = math_formula.replace(
                        col,
                        re.sub(f"[{re.escape(special_chars)}]", "", col),
                        1,
                    )

                # Handle division by zero by replacing zeros with a small number (e.g., 0.001) in the DataFrame
                if "/" in formula_symbols:
                    # Extract the column names involved in division (after '/')
                    div_columns = re.findall(
                        r"(df\['([^']*)'\]|\d+(\.\d+)?)\s*\/\s*df\['([^']*)'\]",
                        formula,
                    )
                    for col_denum in div_columns:
                        df[col_denum[-1]] = df[col_denum[-1]].replace(0, 0.001)

                # Prepare the local_dict with column data
                local_dict = {
                    re.sub(f"[{re.escape(special_chars)}]", "", col)
                    .strip(): df[col]
                    .values
                    for col in numerical_columns
                }

                # Evaluate the formula to update the existing columns or create new one
                if "," in math_formula:
                    # Handle multiple columns in the formula, update existing columns
                    math_formulas = math_formula.split(",")
                    new_feature = ""
                    for col_name in numerical_columns:
                        for col_formula in math_formulas:
                            if (
                                re.sub(f"[{re.escape(special_chars)}]", "", col_name)
                                in col_formula
                            ):
                                # Evaluate the formula and assign it to the new column
                                df[col_name] = ne.evaluate(
                                    col_formula.strip(), local_dict=local_dict
                                )
                else:
                    # Evaluate the formula and assign it to the new column
                    df[new_feature] = ne.evaluate(
                        math_formula.strip(), local_dict=local_dict
                    )
            except Exception as e:
                return {"error": f"Error evaluating formula: {str(e)}"}

        # Perform time conversion and aggregation if necessary
        if "Equal" not in method and interval != "daily":
            if not date_type:
                return {
                    "error": "Time conversion and statistics cannot be performed for non-time series data"
                }
            df, stats_df = aggregate_data(
                df, interval, method, date_type, month, season
            )
        elif "None" not in statistics:
            if not date_type:
                return {
                    "error": "Time conversion and statistics cannot be performed for non-time series data"
                }
            stats_df = calculate_statistics(df, statistics, date_type)

        # Return the data and statistics as dictionaries
        return {
            "data": df.map(round_numeric_values).to_dict(orient="records"),
            "new_feature": new_feature,
            "stats": stats_df.to_dict(orient="records") if stats_df is not None else [],
            "statsColumns": stats_df.columns.tolist() if stats_df is not None else [],
        }
    except Exception as e:
        return {"error": str(e)}


def export_data_service(data, is_empty=False):
    """Export data and statistics to a file in the specified format."""
    try:
        # Fetch the data and statistics from the fetch_data_service
        output = fetch_data_service(data) if not is_empty else {}
        if output.get("error", None):
            return output
        df = pd.DataFrame(output["data"]) if output.get("data", None) else None
        stats_df = (
            pd.DataFrame(output["stats"]) if output.get("statsColumns", None) else None
        )

        # Extract the required parameters from the request data
        output_filename = data.get(
            "export_filename",
            f"exported_data_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        )
        output_format = data.get("export_format", "csv")
        output_path = data.get("export_path", "dataExport")
        # Handle options json stringify
        options = json.loads(data.get("options", "{'table': true, 'stats': true}"))
        columns_list = (
            json.loads(data.get("columns")) if data.get("columns") != "All" else "All"
        )
        id_column = data.get("id_column", "ID")
        date_type = data.get("date_type")
        graph_type = data.get("graph_type", "scatter")
        geojson_data = json.loads(data.get("geojson_data", "{}"))
        feature = data.get("feature", "value")
        feature_statistic = data.get("feature_statistic", "mean")
        default_crs = data.get("default_crs", "EPSG:4326")

        # Parse multi_graph_type
        multi_graph_type = json.loads(data.get("multi_graph_type", "[]"))

        if not multi_graph_type:
            multi_graph_type = [
                {"type": graph_type, "name": column}
                for column in columns_list
                if not column.endswith(id_column) and column != date_type
            ]

        if not date_type:
            return {
                "error": "Graph creation cannot be performed for non-time series data"
            }

        # Save the data and statistics to the specified file format
        # Perform graph creation if the output format is an image or excel format
        file_path = save_to_file(
            df,
            stats_df,
            f"{output_filename}.{output_format}",
            output_format,
            output_path,
            options,
            date_type,
            multi_graph_type,
            geojson_data,
            feature,
            feature_statistic,
            data.get("spatial_scale"),
            default_crs,
            list(map(int, json.loads(data.get("id")))) if data.get("id") != [] else [],
            is_empty,
        )

        return {"file_path": file_path}
    except Exception as e:
        return {"error": str(e)}


def fetch_data_from_db(
    db_path, table_name, selected_ids, columns, start_date, end_date, date_type
):
    """Fetch data from a SQLite database table with real-to-alias mapping."""
    conn = sqlite3.connect(safe_join(Config.PATHFILE, db_path))

    # table_name is an alias so replace it with the real table name
    real_table_name = alias_mapping.get(table_name, {}).get("real", table_name)

    # If specific columns are selected, map them to the real columns
    columns_list = []
    if columns != "All":
        columns_list = columns
        real_columns = [
            f'"{alias_mapping.get(table_name, {}).get("columns", {}).get(col, col)}"'
            for col in columns_list
        ]
        columns = ",".join(real_columns)

    # Start building the base query using real table name
    query = f"SELECT {columns if columns != 'All' else '*'} FROM {real_table_name}"
    params = []

    ID = next((col for col in columns_list if "ID" in col), "ID")

    # Add conditions for selected_ids
    if selected_ids != []:
        placeholders = ",".join(["?"] * len(selected_ids))
        query += f" WHERE {ID} IN ({placeholders})"
        params.extend(selected_ids)

    # Add date range conditions
    if start_date and end_date:
        if selected_ids != []:
            query += f" AND {date_type} BETWEEN ? AND ?"
        else:
            query += f" WHERE {date_type} BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    # Execute the query with parameters
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    # Map real column names back to alias if needed
    alias_columns = [
        (
            alias_mapping.get(real_table_name, {}).get("columns", {}).get(col, col)
            if ID not in col
            else col
        )
        for col in df.columns
    ]
    df.columns = alias_columns

    return df.map(round_numeric_values)


# Helper function to save data to CSV or text formats
def save_to_file(
    dataframe1,
    dataframe2,
    filename,
    file_format,
    export_path,
    options,
    date_type,
    multi_graph_type,
    geojson_data,
    feature,
    feature_statistic,
    spatial_scale,
    default_crs,
    selected_ids=[],
    is_empty=False,
):
    """Save two DataFrames to the specified file format sequentially."""
    # Set the file path
    file_path = (
        safe_join(Config.PATHFILE_EXPORT, export_path)
        if not os.path.isabs(export_path) or os.environ.get("WAITRESS") == "1"
        else export_path
    )

    os.makedirs(file_path, exist_ok=True)
    file_path = safe_join(file_path, filename)

    # Map graph types to Matplotlib Axes methods
    GRAPH_TYPE_MAPPING = {
        "line": "plot",
        "bar": "bar",
        "barx": "column",
        "linex": "line",
        "scatter": "scatter",
    }

    if not is_empty:
        # Check if the dataframe contains an ID column
        ID = next((col for col in dataframe1.columns if "ID" in col), "ID")
        dataframe1[date_type] = pd.to_datetime(dataframe1[date_type]).dt.date

        # Keep track of which axis (primary or secondary) to use for each column
        primary_axis_columns = []
        secondary_axis_columns = []

        # Classify columns based on their value ranges (example threshold: >100 for secondary y-axis)
        selected_columns = [col for col in dataframe1.columns if col != date_type]
        for column in selected_columns:
            if dataframe1[column].max() > 100:
                secondary_axis_columns.append(column)
            else:
                primary_axis_columns.append(column)

    # Write first dataframe and/or statistics dataframe to file with csv/text format
    if file_format == "csv":
        with open(file_path, "w", newline="") as f:
            if options["table"]:
                dataframe1.to_csv(f, index=False)
            if options["stats"] and dataframe2 is not None:
                f.write("\n")
                dataframe2.to_csv(f, index=False)
    elif file_format == "txt":
        with open(file_path, "w") as f:
            if options["table"]:
                dataframe1.to_csv(f, index=False, sep=" ")
            if options["stats"] and dataframe2 is not None:
                f.write("\n")
                dataframe2.to_csv(f, index=False, sep=" ")
    elif file_format == "xlsx":
        # Write the DataFrame to an Excel file
        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            date_type_list = [date_type] if date_type else []
            cols_to_front = [*date_type_list, ID] + [
                col for col in dataframe1.columns if col not in [ID, *date_type_list]
            ]
            dataframe1 = dataframe1[cols_to_front]
            # Sort dataframe by ID column for consistent selection
            dataframe1 = dataframe1.sort_values([ID, *date_type_list])
            # Write the DataFrame to Excel
            dataframe1.to_excel(writer, sheet_name="Sheet1", index=False)

            # Access the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]

            # Initialize the chart object
            chart = None

            # Define chart type and add data for the chart
            for i, column_graph in enumerate(multi_graph_type, start=1):
                multi_graph_type_same = (
                    i > 1 and multi_graph_type[i - 2]["type"] == column_graph["type"]
                )
                overlay_chart = (
                    chart
                    if multi_graph_type_same
                    else workbook.add_chart(
                        {
                            "type": GRAPH_TYPE_MAPPING.get(
                                column_graph["type"] + "x", column_graph["type"]
                            )
                        }
                    )
                )
                column = column_graph["name"]
                row_count = len(dataframe1) + 1

                if selected_ids and selected_ids != []:
                    prev_end_row = 1  # Start from the first data row

                    for j, selected_id in enumerate(selected_ids):
                        # Calculate the start and end rows for the current ID
                        start_row = prev_end_row + 1
                        end_row = (
                            start_row
                            + len(dataframe1[dataframe1[ID] == selected_id])
                            - 1
                        )
                        col_letter = xl_col_to_name(i + 1)

                        # Add a series to the overlay chart
                        overlay_chart.add_series(
                            {
                                "name": f"{column} - {ID}: {selected_id}",
                                "categories": f"Sheet1!$A${start_row}:$A${end_row}",  # Assuming column A contains categories
                                "values": f"Sheet1!${col_letter}${start_row}:${col_letter}${end_row}",
                                "y2_axis": column
                                in secondary_axis_columns,  # Assign to secondary y-axis if applicable
                            }
                        )

                        # Update previous end row
                        prev_end_row = end_row

                else:
                    col_letter = xl_col_to_name(i + 1) if ID else xl_col_to_name(i)
                    # Add a single series for each selected column when selected_ids is empty
                    overlay_chart.add_series(
                        {
                            "name": column,
                            "categories": f"Sheet1!$A$2:$A${row_count}",
                            "values": f"Sheet1!${col_letter}$2:${col_letter}${row_count}",
                            "y2_axis": column in secondary_axis_columns,
                        }
                    )
                if chart is None or multi_graph_type_same:
                    chart = overlay_chart
                else:
                    chart.combine(overlay_chart)
            if not primary_axis_columns or (ID in primary_axis_columns and len(primary_axis_columns) == 1):
                # Add dummy series to primary y-axis if no columns are present
                chart.add_series(
                    {
                        "name": "Dummy",
                        "categories": f"Sheet1!$A$2:$A${row_count}",
                        "values": f"Sheet1!$B$2:$B${row_count}",
                        "y2_axis": False,
                    }
                )        
            
            # Customize the chart
            chart.set_x_axis(
                {
                    "name": date_type,
                    "date_axis": True,
                    "num_format": "yyyy-mm-dd",
                    "major_gridlines": {"visible": True},
                    "num_font": {"rotation": -45},
                    "visible": True,
                }
            )
            primary_y_axis_options = {
                "name": "Values (Smaller Values)",
                "major_gridlines": {"visible": len(primary_axis_columns) > 1},
            }
            chart.set_y_axis(primary_y_axis_options)

            # Configure the secondary Y axis only if it's actually needed
            if secondary_axis_columns:
                chart.set_y2_axis({
                    "name": "Values (Larger Values)",
                    "major_gridlines": {"visible": True}
                    })

            # Insert the chart into the worksheet
            worksheet.insert_chart(f"{xl_col_to_name(len(dataframe1.columns) + 1)}2", chart)
            workbook.close()
    elif file_format in ["png", "jpg", "jpeg", "svg", "pdf"]:
        # Plot each column as a line on the same figure
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()  # Create a secondary y-axis
        # Setting color cycles
        ax1.set_prop_cycle(cycler(color=plt.cm.tab10.colors))
        # Check if ax2 will have plots
        ax2_has_data = any(
            column_graph["name"] not in primary_axis_columns
            for column_graph in multi_graph_type
        )
        if ax2_has_data:
            ax2.set_prop_cycle(cycler(color=plt.cm.Set2.colors))

        for i, column_graph in enumerate(multi_graph_type):
            column = column_graph["name"]
            plot_func = getattr(
                ax1 if column in primary_axis_columns else ax2,
                GRAPH_TYPE_MAPPING[column_graph["type"]],
            )

            if selected_ids and selected_ids != []:
                # Create separate plots for each ID-Column combination
                for j, selected_id in enumerate(selected_ids):
                    filtered_data = dataframe1[dataframe1[ID] == selected_id]
                    plot_func(
                        (
                            filtered_data[date_type] + pd.DateOffset((i + j) * 2)
                            if column_graph["type"] == "bar"
                            else filtered_data[date_type]
                        ),
                        filtered_data[column],
                        label=f"{column} - {ID}: {selected_id}",
                        alpha=0.7,
                    )
            else:
                # Plot each column as a single series if selected_ids is empty
                plot_func(
                    (
                        dataframe1[date_type] + pd.DateOffset(i * 2)
                        if column_graph["type"] == "bar"
                        else dataframe1[date_type]
                    ),
                    dataframe1[column],
                    label=column,
                    alpha=0.7,
                )

        # Customize axes
        ax1.set_xlabel(date_type)
        ax1.set_ylabel("Values (Smaller Values)")
        ax1.xaxis.set_major_locator(MaxNLocator(nbins=30))  # Scale x&y-axis ticks
        ax1.yaxis.set_major_locator(LinearLocator(numticks=8))
        ax1.grid(visible=True, linestyle="--", alpha=0.6)

        if ax2_has_data:
            ax2.set_ylabel("Values (Larger Values)")
            ax2.xaxis.set_major_locator(
                MaxNLocator(nbins=30)
            )  # Ensure same number of x&y-axis ticks on both axes
            ax2.yaxis.set_major_locator(LinearLocator(numticks=8))
            ax2.grid(visible=True, linestyle="--", alpha=0.6)

        ax1.legend(loc="upper left")
        if ax2_has_data:
            ax2.legend(loc="upper right")

        # Rotate x-axis labels (explicitly for ax1 and ax2 if shared x-axis is used)
        for tick in ax1.get_xticklabels():
            tick.set_rotation(45)

        # Adjust layout to avoid label overlap
        plt.tight_layout()

        # Save the plot
        plt.savefig(file_path, format=file_format)
    elif file_format == "shp":
        # Load the GeoJSON dictionary into a GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

        geometry_types = [
            "Point",
            "LineString",
            "Polygon",
            "MultiPolygon",
            "MultiPoint",
            "MultiLineString",
        ]

        # Set CRS if it's not already defined
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", allow_override=True, inplace=True)

        # Reproject the GeoDataFrame to the default CRS
        gdf = gdf.to_crs(default_crs)

        spatial_scale_id_map = {"reach": "id_", "subarea": "gridcode"}

        # Get the ID column name based on the spatial scale
        id_name = spatial_scale_id_map.get(spatial_scale, "id")

        # Find all columns containing "id" (case-insensitive)
        id_columns = [col for col in gdf.columns if id_name in col.lower()]

        # If there are multiple id columns, merge them into a single 'ID' column
        # Initialize the 'ID' column with the first 'id' column
        gdf["ID"] = gdf[id_columns[0]] if len(id_columns) >= 1 else None

        # Loop through the remaining 'id' columns and fill NaNs
        for col in id_columns[1:]:
            gdf["ID"] = gdf["ID"].fillna(gdf[col])

        # Drop all the original 'id' columns
        for col in id_columns:
            gdf.drop(columns=[col], inplace=True)

        if dataframe1 is not None:
            # Rename ID in dataframe1 to match the found id_column in gdf
            dataframe1 = dataframe1.rename(columns={ID: "ID"})

            # Merge the Shapefile data with the attribute DataFrame using the correct ID column
            # Left join to keep all geometries in the Shapefile
            merged_gdf = gdf.merge(
                (
                    pd.DataFrame([])
                    if not feature or feature == "value"
                    else dataframe1.groupby("ID")[feature]
                    .agg(feature_statistic)
                    .reset_index()
                ),
                on="ID",
                how="left",
            )
        else:
            merged_gdf = gdf

        # Use a dictionary to store the filtered GeoDataFrames by geometry type
        gdf_dict = {
            geom: merged_gdf[merged_gdf.geom_type == geom] for geom in geometry_types
        }

        base_filename = os.path.splitext(file_path)[0]

        # List of GeoDataFrames and their corresponding suffixes
        geometry_and_suffixes = [
            (
                gdf_geom.dropna(how="all", axis=1).dropna(how="all", axis=0),
                f"_{gdf_geom.geom_type.iloc[0].lower()}",
            )
            for gdf_geom in gdf_dict.values()
            if not gdf_geom.empty
        ]

        # Save the GeoDataFrames to Shapefiles and create a zip file
        save_data_and_create_zip(geometry_and_suffixes, base_filename, file_path)

        file_path = f"{base_filename}.zip"

    return file_path


def save_geospatial_data(gdf_geom, suffix, base_filename):
    """Function to save geospatial data (e.g., Shapefiles)."""
    gdf_geom.to_file(f"{base_filename}{suffix}.shp", driver="ESRI Shapefile")


def save_data_and_create_zip(geometry_and_suffixes, base_filename, file_path):
    # First thread pool for saving geospatial data
    with ThreadPoolExecutor() as executor:
        # Unpack the geometry and suffixes and save the geospatial data
        executor.map(
            lambda args: save_geospatial_data(*args, base_filename),
            geometry_and_suffixes,
        )

    # Create the zip file sequentially
    file_paths = []
    for root, _, files in os.walk(os.path.dirname(file_path)):
        for file in files:
            if not file.endswith(".zip"):
                file_paths.append(os.path.join(root, file))

    # Now zip the files
    with ZipFile(f"{base_filename}.zip", "w", compression=ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            arcname = os.path.relpath(file_path, os.path.dirname(file_path))
            zipf.write(file_path, arcname)


def get_table_names(data):
    """
    Get the names of all tables in a SQLite database.
    """
    try:
        db_path = data.get("db_path")
        conn = sqlite3.connect(safe_join(Config.PATHFILE, db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        # Map real table names to alias names
        alias_tables = [
            alias_mapping.get(table[0], {}).get("alias", table[0]) for table in tables
        ]
        return {"tables": alias_tables}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def get_files_and_folders(data):
    """
    Construct a tree of folders and files within a given folder path.
    """

    folder_tree = set()
    folder_path = data.get("folder_path", "Jenette_Creek_Watershed")
    global bmp_db_path_global

    if (
        os.path.isabs(folder_path)
        and data.get("is_tauri", None) == "true"
        and os.environ.get("WAITRESS") != "1"
    ):
        # Update Config.PATHFILE to point to the parent directory of the provided absolute path
        Config.PATHFILE = os.path.dirname(folder_path)
        base_path = Config.PATHFILE
    elif os.path.isabs(folder_path):
        return {
            "error": "The folder path cannot be absolute when not using the Tauri app."
        }
    else:
        # Determine the base path of the application
        base_path = (
            (
                sys._MEIPASS  # When the application is packaged with PyInstaller
                if getattr(sys, "frozen", False)
                else os.path.dirname(__file__)
            )
            if folder_path == "Jenette_Creek_Watershed"
            else Config.PATHFILE
        )
        # Construct the absolute folder path relative to the current file location
        folder_path = safe_join(base_path, folder_path)

    try:
        files_and_folders = []
        lookup_found = False

        for dirpath, dirs, files in os.walk(folder_path):
            # Construct the relative path from the base folder
            rel_dir = os.path.relpath(dirpath, base_path)

            # Append directories
            for fdir in dirs:
                dir_rel_path = os.path.join(rel_dir, fdir)
                files_and_folders.append(
                    {
                        "type": "folder",
                        "name": dir_rel_path,
                    }
                )
            # Append files
            for name in files:
                file_rel_path = os.path.join(rel_dir, name)

                # Only include .shp, .db3, and .tif files
                if file_rel_path.endswith(
                    (".shp", ".db3", ".tif", ".tiff")
                ) and not file_rel_path.endswith("reprojected.tif"):
                    if file_rel_path.endswith(".db3") and "lookup" not in file_rel_path:
                        folder_tree.add(os.path.join(Config.PATHFILE, file_rel_path))
                    elif file_rel_path.endswith(".db3") and "lookup" in file_rel_path:
                        Config.LOOKUP = file_rel_path
                        lookup_found = True
                    if "bmp" in file_rel_path.lower():
                        bmp_db_path_global = file_rel_path.replace("\\", "/")
                    files_and_folders.append(
                        {
                            "type": (
                                "database" if file_rel_path.endswith(".db3") else "file"
                            ),
                            "name": file_rel_path,
                        }
                    )
        # Load alias mapping for each database
        (
            alias_mapping.update(load_alias_mapping(folder_tree))
            if not alias_mapping and lookup_found
            else None
        )

        return {"files_and_folders": files_and_folders}
    except Exception as e:
        return {"error": str(e)}

def get_season_from_date(date_str):
    """Map date strings to seasons."""
    month = date_str.month
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    elif month in [9, 10, 11]:
        return "Autumn"


# Helper function to apply time interval aggregation
def aggregate_data(df, interval, method, date_type, month, season):
    """Aggregate data based on the specified interval and method."""
    # Convert the date_type column to datetime
    df[date_type] = pd.to_datetime(df[date_type])
    resampled_df = None
    ID = next((col for col in df.columns if "ID" in col), "ID")
    # Resample the data based on the specified interval
    if interval == "monthly":
        # Agrregate numerical values by summing for each ID, date_type, and interval
        resampled_df = df.groupby([ID, pd.Grouper(key=date_type, freq="ME")]).sum(
            numeric_only=True
        )
        if month:
            resampled_df = resampled_df[
                resampled_df.index.get_level_values(date_type).month == int(month)
            ]
    elif interval == "yearly":
        resampled_df = df.groupby([ID, pd.Grouper(key=date_type, freq="YE")]).sum(
            numeric_only=True
        )
    elif interval == "seasonally":
        # Custom resampling for seasons
        df["Season"] = df[date_type].apply(lambda x: get_season_from_date(x))

        # Quarterly year starts in December resampling for seasons
        # DJF, MAM, JJA, SON
        resampled_df = df.groupby(
            [ID, "Season", pd.Grouper(key=date_type, freq="QS-DEC")]
        ).sum(numeric_only=True)
        if season:
            resampled_df = resampled_df[resampled_df["Season"] == season.title()]
    else:
        resampled_df = df

    # Reset the index to convert the MultiIndex to columns
    resampled_df.reset_index(inplace=True)

    # Format the date column based on the interval
    if interval != "daily":
        resampled_df[date_type] = (
            resampled_df[date_type].dt.strftime("%Y")
            if interval == "yearly"
            else resampled_df[date_type].dt.strftime("%Y-%m")
        )
    else:
        resampled_df[date_type] = resampled_df[date_type].dt.strftime("%Y-%m-%d")
    stats_df = calculate_statistics(resampled_df, method, date_type)

    return resampled_df.map(round_numeric_values), stats_df.map(round_numeric_values)


def round_numeric_values(value):
    """
    Round numeric values to 4 decimal places if they are small (less than 0.01),
    otherwise round to 2 decimal places.
    """
    if isinstance(value, (float, int)):  # Check if the value is a number
        if abs(value) < 0.01:  # Small values
            return round(value, 4)
        else:  # Larger values
            return round(value, 2)
    return value


def calculate_statistics(df, statistics, date_type):
    """Calculate specified statistics for numerical data in the DataFrame."""
    stats_df = pd.DataFrame()

    # Store the original DataFrame with all columns
    original_df = df.copy()

    # Select only numerical columns for calculations
    df = df.select_dtypes(include=["number"])
    # Drop the date_type column if it exists
    df = df.drop(columns=[date_type], errors="ignore")

    if "Average" in statistics:
        stats_df["Average"] = df.mean()
    if "Sum" in statistics:
        stats_df["Sum"] = df.sum()
    if "Maximum" in statistics:
        stats_df["Maximum"] = df.max()
        # Use original DataFrame to get the corresponding date_type values for maximums
        # Ignore if date_type is not present in the original DataFrame
        max_date_type = {
            col: original_df.loc[original_df[col].idxmax(), date_type]
            for col in df.columns
            if date_type in original_df.columns
        }
        stats_df[f"Maximum {date_type}"] = pd.Series(max_date_type)
    if "Minimum" in statistics:
        stats_df["Minimum"] = df.min()
        # Use original DataFrame to get the corresponding date_type values for minimums
        # Ignore if date_type is not present in the original DataFrame
        min_date_type = {
            col: original_df.loc[original_df[col].idxmin(), date_type]
            for col in df.columns
            if date_type in original_df.columns
        }
        stats_df[f"Minimum {date_type}"] = pd.Series(min_date_type)
    if "Standard Deviation" in statistics:
        stats_df["Standard Deviation"] = df.std()

    # Transpose and format DataFrame
    stats_df = stats_df.T
    stats_df.reset_index(inplace=True)
    stats_df.rename(columns={"index": "Statistics"}, inplace=True)

    return stats_df.map(round_numeric_values)


def load_alias_mapping(folder_tree):
    """Load alias mapping from the lookup.db3 database."""
    conn = sqlite3.connect(os.path.join(Config.PATHFILE, Config.LOOKUP))
    alias_map = {}

    # Query the alias tables (Hydroclimate, BMP, scenario_2)
    for table in folder_tree:
        # Extract the table name from the path
        table = os.path.basename(table).replace(".db3", "")

        query = f"SELECT * FROM {table}"
        df = pd.read_sql_query(query, conn)

        for _, row in df.iterrows():
            real_table = row["Table Name"]
            alias_table = row["Table Alias"]
            real_column = row["Column Name"]
            alias_column = row["Column Alias"]

            # Map real-to-alias and alias-to-real for both tables and columns
            alias_map.setdefault(real_table, {}).setdefault("alias", alias_table)
            alias_map[real_table].setdefault("columns", {})[real_column] = alias_column
            alias_map.setdefault(alias_table, {}).setdefault("real", real_table)
            alias_map[alias_table].setdefault("columns", {})[alias_column] = real_column

    conn.close()
    return alias_map


def get_columns_and_time_range(db_path, table_name):
    """Fetch column names and time range from a SQLite database table with real-to-alias mapping."""

    try:
        # Convert the table alias to its real name if necessary
        real_table_name = alias_mapping.get(table_name, {}).get("real", table_name)

        # Connect to the database
        conn = sqlite3.connect(safe_join(Config.PATHFILE, db_path))

        # Fetch column information using PRAGMA for the real table name
        query = f"PRAGMA table_info('{real_table_name}')"
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [row[1] for row in cursor.fetchall()]

        # Convert real column names to alias names (if available in the mapping)
        alias_columns = [
            alias_mapping.get(real_table_name, {}).get("columns", {}).get(col, col)
            for col in columns
        ]

        # Initialize variables
        start_date = end_date = date_type = interval = None

        # Check and query for specific date/time columns (using real column names)
        for date_col, dtype, inter in [
            ("Time", "Time", "daily"),
            ("Date", "Time", "daily"),
            ("Month", "Month", "monthly"),
            ("Year", "Year", "yearly"),
        ]:
            if date_col in columns:
                df = pd.read_sql_query(
                    f"SELECT {date_col} FROM {real_table_name}", conn
                )
                if date_col in ["Time", "Date"]:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                    start_date = df[date_col].min().strftime("%Y-%m-%d")
                    end_date = df[date_col].max().strftime("%Y-%m-%d")
                elif date_col in ["Month", "Year"]:
                    start_date = int(df[date_col].min())
                    end_date = int(df[date_col].max())
                date_type = dtype
                interval = inter
                break

        # Get list of IDs if an ID column exists, without querying unnecessary data
        id_column = next((col for col in columns if "ID" in col), None)
        ids = []
        if id_column:
            id_query = f"SELECT DISTINCT {id_column} FROM {real_table_name}"
            id_df = pd.read_sql_query(id_query, conn)
            ids = id_df[id_column].tolist()

        # Return alias column names instead of real ones
        return {
            "columns": alias_columns,
            "start_date": start_date,
            "end_date": end_date,
            "id_column": id_column or "",
            "ids": ids,
            "date_type": date_type,
            "interval": interval,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def get_multi_columns_and_time_range(data):
    """Fetch column names and time range from multiple SQLite database tables."""
    try:
        db_tables = json.loads(data.get("db_tables"))
        multi_columns_time_range = []
        all_columns = set()

        for table in db_tables:
            table_key = f"{(table['db'], table['table'])}"

            columns_time_range = get_columns_and_time_range(table["db"], table["table"])

            if columns_time_range.get("error"):
                return columns_time_range

            # Rename columns if they are duplicates by prefixing with the table name and a dash
            prefixed_columns = [
                (
                    f"{table['table']}-{col}"
                    if col in all_columns
                    and col != columns_time_range["date_type"]
                    and "id" not in col.lower()
                    else col
                )
                for col in columns_time_range["columns"]
            ]

            all_columns.update(columns_time_range["columns"])

            # Store columns for each table in a global dictionary
            global_dbs_tables_columns[table_key] = (
                columns_time_range["columns"] + [columns_time_range["id_column"]]
                if columns_time_range["ids"] != []
                else columns_time_range["columns"]
            )

            multi_columns_time_range.append(
                {**columns_time_range, "columns": prefixed_columns}
            )

        # Verify each entry in global_dbs_tables_columns against db_tables
        existing_keys = {f"{(table['db'], table['table'])}" for table in db_tables}

        keys_to_delete = [
            key for key in global_dbs_tables_columns.keys() if key not in existing_keys
        ]
        # Delete keys that do not exist in db_tables
        for key in keys_to_delete:
            del global_dbs_tables_columns[key]

        # Check consistency across tables for date_type, interval, start_date, end_date, and ids
        keys_to_check = ["date_type", "interval", "id_column"]
        for key in keys_to_check:
            unique_values = set(table[key] for table in multi_columns_time_range)
            if len(unique_values) > 1:
                return {"error": f"Tables have different {key.replace('_', ' ')}"}

        # Intersection of start and end dates from all tables
        start_dates = [table["start_date"] for table in multi_columns_time_range]
        end_dates = [table["end_date"] for table in multi_columns_time_range]
        id_column = [table["id_column"] for table in multi_columns_time_range][
            0
        ]  # Assuming all tables have the same ID column
        start_date = max(start_dates)
        end_date = min(end_dates)

        # Combine all columns with date_type as first column
        columns = (
            [multi_columns_time_range[0]["date_type"]]
            if multi_columns_time_range[0]["date_type"]
            else []
        )

        # Check if ID column is present in any of the tables
        include_id = any(
            table.get("ids", []) != [] for table in multi_columns_time_range
        )

        if include_id:
            columns.append(id_column or "ID")

        # Add all other columns from each table
        columns += [
            col
            for table in multi_columns_time_range
            for col in table["columns"]
            if col
            not in [
                multi_columns_time_range[0]["date_type"],
                id_column or "ID",
            ]
            and (id_column or "ID") not in col
        ]

        # Intersection of IDs from all tables
        ids = set(multi_columns_time_range[0]["ids"]).intersection(
            *[set(table["ids"]) for table in multi_columns_time_range]
        )

        return {
            "columns": columns,
            "global_columns": global_dbs_tables_columns,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "id_column": id_column or "ID",
            "ids": [str(id) for id in sorted(ids)],
            "date_type": multi_columns_time_range[0]["date_type"] or "",
            "interval": multi_columns_time_range[0]["interval"] or "",
        }
    except Exception as e:
        return {"error": str(e)}


def round_coordinates(geojson_data, decimal_points=4):
    """
    Recursively round all coordinates in the GeoJSON to a specified number of decimal points.
    """

    def round_coords(coords):
        if isinstance(coords[0], list):
            # If the first element is a list, recurse (for MultiPolygon, Polygon, etc.)
            return [round_coords(c) for c in coords]
        else:
            # Otherwise, round the coordinates (for Point, etc.)
            return [round(coord, decimal_points) for coord in coords]

    if isinstance(geojson_data, str):
        geojson_data = json.loads(geojson_data)

    for feature in geojson_data.get("features", []):
        geometry = feature.get("geometry", {})
        if "coordinates" in geometry:
            geometry["coordinates"] = round_coords(geometry["coordinates"])

    return geojson_data


def bounds_overlap_or_similar(bounds1, bounds2, tolerance=0.0001):
    """
    Check if two bounds are overlapping, contained, or in the same location.
    If similar, return the larger bound; if far apart, return the first bound.
    """

    if not bounds1:
        return True, bounds2

    # Unpack bounds
    minY1, minX1 = bounds1[0]
    maxY1, maxX1 = bounds1[1]
    minY2, minX2 = bounds2[0]
    maxY2, maxX2 = bounds2[1]

    # Adjust for tolerance
    minY1 -= tolerance
    minX1 -= tolerance
    maxY1 += tolerance
    maxX1 += tolerance

    minY2 -= tolerance
    minX2 -= tolerance
    maxY2 += tolerance
    maxX2 += tolerance

    # Check for overlap (intersection)
    horizontal_overlap = not (maxX1 < minX2 or maxX2 < minX1)
    vertical_overlap = not (maxY1 < minY2 or maxY2 < minY1)

    if horizontal_overlap and vertical_overlap:
        # Merge to create a larger bounding box
        merged_bounds = [
            [min(minY1, minY2), min(minX1, minX2)],
            [max(maxY1, maxY2), max(maxX1, maxX2)],
        ]
        return True, merged_bounds  # Overlapping bounds merged

    # Check for containment (one inside another)
    is_contained = (
        minX1 >= minX2 and maxX1 <= maxX2 and minY1 >= minY2 and maxY1 <= maxY2
    ) or (minX2 >= minX1 and maxX2 <= maxX1 and minY2 >= minY1 and maxY2 <= maxY1)

    if is_contained:
        # Return the larger bound
        area1 = (maxX1 - minX1) * (maxY1 - minY1)
        area2 = (maxX2 - minX2) * (maxY2 - minY2)
        return True, bounds1 if area1 >= area2 else bounds2

    # Check if centers are very close (proximity)
    center1 = [(minX1 + maxX1) / 2, (minY1 + maxY1) / 2]
    center2 = [(minX2 + maxX2) / 2, (minY2 + maxY2) / 2]

    center_distance = (
        (center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2
    ) ** 0.5

    if center_distance < tolerance:
        # Merge if centers are close
        merged_bounds = [
            [min(minY1, minY2), min(minX1, minX2)],
            [max(maxY1, maxY2), max(maxX1, maxX2)],
        ]
        return True, merged_bounds

    # If completely far apart, return the first bound
    return False, bounds1


def get_raster_normalized(band):
    """
    Normalize a raster band by computing the min and max values while ignoring NoData values.
    """
    # Read raster data as a NumPy array
    raster_data = band.ReadAsArray()

    # Get the NoData value
    no_data_value = band.GetNoDataValue()

    # Mask NoData values if present
    if no_data_value is not None:
        raster_data = np.ma.masked_equal(raster_data, no_data_value)

    # Compute min and max while ignoring NoData
    raster_min = (
        np.min(raster_data) if np.ma.is_masked(raster_data) else np.nanmin(raster_data)
    )
    raster_max = (
        np.max(raster_data) if np.ma.is_masked(raster_data) else np.nanmax(raster_data)
    )

    # Normalize the raster while avoiding division by zero
    if raster_max - raster_min == 0:
        raster_normalized = np.zeros_like(
            raster_data
        )  # If constant values, return all zeros
    else:
        raster_normalized = (raster_data - raster_min) / (raster_max - raster_min)

    return raster_data, raster_normalized, raster_min, raster_max


def get_raster_color_levels(band, colormap, num_classes=5):
    """
    Generate color levels for a raster band, using its native color mapping.
    """
    _, _, min_value, max_value = get_raster_normalized(band)

    if min_value == max_value:
        return []  # Avoid division by zero for constant rasters

    # Define classification breakpoints
    levels = np.linspace(min_value, max_value, num_classes + 1)

    # Get color values from the colormap
    cmap = plt.get_cmap(colormap, num_classes)
    colors = [mcolors.to_hex(cmap(i / (num_classes - 1))) for i in range(num_classes)]

    # Create the color level mapping
    color_levels = [
        {
            "min": round(levels[i].item(), 2),
            "max": round(levels[i + 1].item(), 2),
            "color": colors[i],
        }
        for i in range(num_classes)
    ]

    return color_levels


def get_metadata_colormap(band):
    """
    Determine an appropriate colormap based on raster metadata.
    """
    metadata = band.GetMetadata()
    colormap_name = metadata.get("COLOR_MAP", "gray")  # Default to "gray" if missing

    if colormap_name not in plt.colormaps():
        colormap_name = "gray"  # Fallback to terrain if unknown

    return plt.get_cmap(colormap_name)


def get_geojson_metadata(geojson_path):
    """Extract metadata from an existing GeoJSON file."""
    if not os.path.exists(geojson_path):
        return None

    with open(geojson_path, "r") as file:
        geojson_data = json.load(file)

    features = geojson_data.get("features", [])
    feature_count = len(features)

    bbox = geojson_data.get("bbox", [])

    if bbox:
        x_min, x_max, y_min, y_max = bbox[0], bbox[2], bbox[1], bbox[3]
    else:
        x_min, x_max, y_min, y_max = (
            float("inf"),
            float("-inf"),
            float("inf"),
            float("-inf"),
        )

    field_names = []

    for feature in features:
        geom = feature.get("geometry", {})
        props = feature.get("properties", {})
        # Collect property field names
        field_names.extend(list(props.keys()))

    return {
        "feature_count": feature_count,
        "extent": (round(x_min, 6), round(x_max, 6), round(y_min, 6), round(y_max, 6)),
        "field_names": list(dict.fromkeys(field_names)),
    }


def generate_dynamic_colors(values, colormap_name, num_classes=5):
    """
    Generate dynamic colors based on feature column values using a colormap.
    """
    colormap = cm.get_cmap(
        colormap_name, num_classes
    )  # Get colormap with `num_classes` bins
    norm = mcolors.Normalize(vmin=min(values), vmax=max(values))  # Normalize values
    colors = [
        mcolors.to_hex(colormap(norm(level)))
        for level in np.linspace(min(values), max(values), num_classes)
    ]
    return colors


def get_colormap_name(feature):
    """Automatically selects the best colormap for a given feature string."""
    feature = feature.lower().replace("_", " ").split(" ")  # Normalize feature name

    feature_colormap_map = {
        # Hydrology & Climate
        "precipitation": "YlGnBu",
        "rainfall": "YlGnBu",
        "p": "YlGnBu",
        "p_net": "YlGnBu",
        "p_blow": "YlGnBu",
        "surface runoff": "PuBu",
        "runoff": "PuBu",
        "qout_m3": "PuBu",
        "qout_mm": "PuBu",
        "flooding": "Blues",
        "temperature": "RdYlBu_r",
        "air temperature": "RdYlBu_r",
        "soil temperature": "RdYlBu_r",
        "humidity": "BuGn",
        "drought": "BrBG",
        "soil moisture": "BrBG",
        "evaporation": "Oranges",
        "wind speed": cmocean.cm.speed,
        # Water Quality & Pollution
        "air quality": "RdYlGn_r",
        "air pollution": "RdYlGn_r",
        "pm2.5": "RdYlGn_r",
        "ozone": "RdYlGn_r",
        "co2": "OrRd",
        "chlorophyll": cmocean.cm.algae,
        "chla": cmocean.cm.algae,
        "cbod": "PuRd",
        "dissolved oxygen": "coolwarm",
        "nh3": "YlOrBr",
        "no2": "YlOrBr",
        "no3": "YlOrBr",
        "organic nitrogen": "BuPu",
        "organic phosphorus": "BuPu",
        "sediment": "Greys",
        # Geography & Terrain
        "elevation": "terrain",
        "altitude": "terrain",
        "topography": "terrain",
        "bathymetry": cmocean.cm.deep,
        # Environmental & Vegetation
        "vegetation": "Greens",
        "ndvi": "PiYG",
        "land cover": "tab10",
        "forest density": "Greens",
        "soil moisture": "BrBG",
        # Other Scientific Data
        "population density": "Purples",
    }

    # Generate combinations of features, keeping order intact
    for r in [1, 2]:  # Only generate combinations of length 1 and 2
        for combo in itertools.combinations(feature, r):
            combined_feat = " ".join(combo)
            if combined_feat in feature_colormap_map:
                return feature_colormap_map[combined_feat]

    # If no match found, return default "viridis"
    return "viridis"


def fetch_geojson_colors(data):
    """
    Fetches data from `fetch_data_service`, applies feature statistics, and generates geojson color mapping.
    """
    # Step 1: Fetch raw data
    output = fetch_data_service(data)
    new_feature = output.get("new_feature", None)
    feature = new_feature or data.get("feature", "value")
    feature_statistic = data.get("feature_statistic", "mean")

    if not feature or feature == "value":
        return {}

    if output.get("error", None):
        return output

    if "data" not in output:
        return {"error": "No data found"}

    df = pd.DataFrame(output["data"])
    ID = next((col for col in df.columns if "ID" in col), None)

    if ID is None:
        return {"error": "No ID column found in data"}

    # Ensure feature column exists
    if feature not in df.columns:
        return {"error": f"Feature column '{feature}' not found in data"}

    feature_df = df.groupby(ID)[feature].agg(feature_statistic).reset_index()

    # Step 3: Decide binning strategy based on skewness
    skewness = skew(feature_df[feature].dropna())
    binning_strategy = (
        "quantile" if abs(skewness) > 1 else "uniform"
    )  # Threshold for skewness

    # Apply the chosen binning strategy
    num_classes = 5
    discretizer = KBinsDiscretizer(
        n_bins=num_classes, encode="ordinal", strategy=binning_strategy
    )
    feature_df["color_class"] = discretizer.fit_transform(feature_df[[feature]]).astype(
        int
    )

    # Get bin edges
    bin_edges = discretizer.bin_edges_[0]  # 6 bin edges for 5 bins

    # Step 4: Generate 5 Colors Based on Quantile Bins
    dynamic_colors = generate_dynamic_colors(
        feature_df[feature].values, get_colormap_name(feature), num_classes=num_classes
    )

    if len(bin_edges) != 6:
        return {"error": "Error generating color levels as the data rows are <= 5."}
    elif np.any(np.isinf(bin_edges)):
        return {
            "error": "Error generating color levels as minimum values are all constant values."
        }

    # Step 5: Create 5 Color Levels Using
    color_levels = [
        {
            "min": round_numeric_values(bin_edges[i]),
            "max": round_numeric_values(bin_edges[i + 1]),
            "color": dynamic_colors[i],
        }
        for i in range(num_classes)
    ]

    # Step 6: Assign Colors to Each ID Based on Their Bin
    geojson_colors = {
        row[ID]: [dynamic_colors[int(row["color_class"])], row["color_class"] + 2]
        for _, row in feature_df.iterrows()
    }

    return {
        "geojson_colors": geojson_colors,
        "geojson_color_levels": color_levels,
        "new_feature": new_feature,
    }


def process_geospatial_data(data):
    """
    Process a geospatial file (shapefile or raster) and return GeoJSON/Tiff Image Url, bounds, and center.
    """

    file_paths = map(
        lambda x: safe_join(Config.PATHFILE, x), json.loads(data.get("file_paths"))
    )
    combined_geojson = {}
    combined_bounds = None
    raster_color_levels = []
    combined_properties = []
    tool_tip = {}
    image_urls = []
    default_crs = None

    for file_path in file_paths:
        toolTipKey = f"{(os.path.basename(file_path),os.path.basename(file_path))}"
        # Check if the file is a shapefile (.shp)
        if file_path.endswith(".shp"):
            # Open shapefile
            driver = ogr.GetDriverByName("ESRI Shapefile")
            dataset = driver.Open(file_path, 0)
            if dataset is None:
                continue

            layer = dataset.GetLayer()

            # Handle Spatial Reference System
            source_srs = layer.GetSpatialRef()
            if source_srs:
                authority_name = source_srs.GetAuthorityName(None)
                authority_code = source_srs.GetAuthorityCode(None)

                if authority_name and authority_code:
                    default_crs = f"{authority_name}:{authority_code}"
                else:
                    default_crs = "EPSG:4326"
            else:
                source_srs = osr.SpatialReference()
                source_srs.ImportFromEPSG(26917)  # Default UTM Zone 17N if unspecified
                default_crs = "EPSG:26917"

            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)  # WGS84 (longitude/latitude)

            # Ensure the axis order is longitude-latitude
            if target_srs.SetAxisMappingStrategy:
                target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

            coord_transform = osr.CoordinateTransformation(source_srs, target_srs)

            # Create a new memory layer for the reprojected data
            memory_driver = ogr.GetDriverByName("Memory")
            memory_ds = memory_driver.CreateDataSource("reprojected")
            reprojected_layer = memory_ds.CreateLayer(
                "reprojected_layer", srs=target_srs, geom_type=layer.GetGeomType()
            )

            # Copy fields from the original layer
            layer_defn = layer.GetLayerDefn()
            for i in range(layer_defn.GetFieldCount()):
                reprojected_layer.CreateField(layer_defn.GetFieldDefn(i))

            # Collect properties dynamically
            properties = [
                layer_defn.GetFieldDefn(i).GetName()
                for i in range(layer_defn.GetFieldCount())
            ]

            # Reproject features in batches if needed
            feature_buffer = []
            BATCH_SIZE = 1000
            for feature in layer:
                geom = feature.GetGeometryRef()
                if geom:
                    geom.Transform(coord_transform)  # Transform geometry to WGS84

                # Create a new feature and store in buffer
                reprojected_feature = ogr.Feature(reprojected_layer.GetLayerDefn())
                reprojected_feature.SetGeometry(geom)
                for i in range(feature.GetFieldCount()):
                    reprojected_feature.SetField(i, feature.GetField(i))

                feature_buffer.append(reprojected_feature)

                # Bulk insert when buffer reaches batch size
                if len(feature_buffer) >= BATCH_SIZE:
                    reprojected_layer.StartTransaction()
                    for f in feature_buffer:
                        reprojected_layer.CreateFeature(f)
                    reprojected_layer.CommitTransaction()
                    feature_buffer.clear()

            # Insert remaining features
            if feature_buffer:
                reprojected_layer.StartTransaction()
                for f in feature_buffer:
                    reprojected_layer.CreateFeature(f)
                reprojected_layer.CommitTransaction()

            # Calculate bounds in WGS84
            extent = reprojected_layer.GetExtent()  # (minX, maxX, minY, maxY)

            x_min = extent[0]
            y_min = extent[2]
            x_max = extent[1]
            y_max = extent[3]

            # Swap longitude & latitude order for Leaflet (Leaflet expects [[minY, minX], [maxY, maxX]])
            bounds = [
                [y_min, x_min],
                [y_max, x_max],
            ]

            shp_metadata = {
                "feature_count": reprojected_layer.GetFeatureCount(),
                "extent": (
                    round(x_min, 6),
                    round(x_max, 6),
                    round(y_min, 6),
                    round(y_max, 6),
                ),
                "field_names": properties,
            }
            geojson_metadata = {}
            geojson_path = os.path.join(
                Config.TEMPDIR, os.path.basename(file_path) + "_output.geojson"
            )

            # Check if a GeoJSON file already exists and extract metadata
            if os.path.exists(geojson_path):
                geojson_metadata = get_geojson_metadata(geojson_path)

            if shp_metadata != geojson_metadata:
                # Convert reprojected layer to GeoJSON
                geojson_driver = ogr.GetDriverByName("GeoJSON")

                geojson_dataset = geojson_driver.CreateDataSource(geojson_path)
                geojson_dataset.CopyLayer(
                    reprojected_layer,
                    "layer",
                    ["RFC7946=YES", "WRITE_BBOX=YES"],
                )
                geojson_dataset = None

            with open(geojson_path, "r") as file:
                geojson_data = json.load(file)

            # Update the combined bounds
            (overlap, combined_bounds) = bounds_overlap_or_similar(
                combined_bounds, bounds
            )

            # Add GeoJSON data/properties to the combined GeoJSON/properties only if the combined bounds are not far apart
            if overlap:
                if combined_geojson:

                    def append_features(geojson_data):
                        """Efficiently append features to GeoJSON."""
                        for feature in geojson_data["features"]:
                            yield feature

                    # Append features to the combined GeoJSON using generator
                    for feature in append_features(geojson_data):
                        combined_geojson["features"].append(feature)
                else:
                    combined_geojson = geojson_data
                if combined_properties:
                    combined_properties.extend(properties)
                else:
                    combined_properties = properties

            # Save properties for each shapefile path
            tool_tip[toolTipKey] = properties
        # Handle GeoTIFF files
        elif file_path.endswith(".tif") or file_path.endswith(".tiff"):
            raster_dataset = gdal.Open(file_path)
            if not raster_dataset:
                continue

            # Ensure raster is in EPSG:4326 (WGS84)
            source_srs = osr.SpatialReference()
            source_srs.ImportFromWkt(raster_dataset.GetProjection())
            if source_srs:
                authority_name = source_srs.GetAuthorityName(None)
                authority_code = source_srs.GetAuthorityCode(None)

                if authority_name and authority_code:
                    default_crs = f"{authority_name}:{authority_code}"
                else:
                    default_crs = "EPSG:4326"
            else:
                source_srs = osr.SpatialReference()
                source_srs.ImportFromEPSG(26917)  # Default UTM Zone 17N if unspecified
                default_crs = "EPSG:26917"
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)

            # Ensure the axis order is longitude-latitude
            if target_srs.SetAxisMappingStrategy:
                target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

            if not source_srs.IsSame(target_srs):
                # Reproject the raster to EPSG:4326
                reprojected_file_path = os.path.join(
                    Config.TEMPDIR, os.path.basename(file_path) + "_reprojected.tif"
                )
                (
                    gdal.Warp(reprojected_file_path, raster_dataset, dstSRS="EPSG:4326")
                    if not os.path.exists(reprojected_file_path)
                    else None
                )
                raster_dataset = gdal.Open(reprojected_file_path)
            else:
                reprojected_file_path = file_path

            # Get raster metadata
            geotransform = raster_dataset.GetGeoTransform()

            x_min = geotransform[0]
            y_max = geotransform[3]
            x_max = x_min + geotransform[1] * raster_dataset.RasterXSize
            y_min = y_max + geotransform[5] * raster_dataset.RasterYSize

            # Calculate bounds for Leaflet
            bounds = [
                [y_min, x_min],
                [y_max, x_max],
            ]

            output_image_path = os.path.join(
                Config.TEMPDIR, os.path.basename(file_path) + "_rendered.png"
            )

            # Read raster data and render to an image
            band = raster_dataset.GetRasterBand(1)  # Use the first raster band
            # Get colormap based on metadata
            cmap = get_metadata_colormap(band)

            if not os.path.exists(output_image_path):
                raster_data, raster_normalized, _, _ = get_raster_normalized(band)

                rgba_colored = cmap(raster_normalized)  # Apply colormap (RGBA values)

                # Convert to uint8 format (0-255)
                rgba_image = (rgba_colored[:, :, :4] * 255).astype(np.uint8)

                # Set the alpha channel for transparency (No-data = Transparent)
                rgba_image[..., 3] = np.where(raster_data.mask, 0, 255)

                # Convert the RGBA array to an image
                color_ramp = Image.fromarray(rgba_image, mode="RGBA")

                # Save the rendered image with transparency
                color_ramp.save(output_image_path, "PNG", quality=95)

            # Get color levels for the raster band
            raster_color_levels = get_raster_color_levels(band, cmap)

            raster_dataset = None

            # Update the combined bounds
            (overlap, combined_bounds) = bounds_overlap_or_similar(
                combined_bounds, bounds
            )

            # Save the image URL for each GeoTIFF path only if the combined bounds are not far apart
            if overlap:
                image_urls.append(f"/api/geotiff/{os.path.basename(output_image_path)}")
        else:
            return {
                "error": "Unsupported file type. Only .shp and .tif/.tiff are supported."
            }

    # Define a function to get a sorting key based on geometry type
    def get_geometry_order(feature):
        geometry_type = feature["geometry"]["type"]
        order = {
            "Polygon": 1,
            "MultiPolygon": 1,
            "LineString": 2,
            "MultiLineString": 2,
            "Point": 3,
            "MultiPoint": 3,
        }
        return order.get(geometry_type, float("inf"))  # Default to last if unknown type

    if combined_geojson:
        combined_geojson["features"] = sorted(
            combined_geojson["features"], key=get_geometry_order
        )
    return {
        "geojson": combined_geojson,
        "bounds": combined_bounds,
        "center": (
            [
                (combined_bounds[0][0] + combined_bounds[1][0]) / 2,
                (combined_bounds[0][1] + combined_bounds[1][1]) / 2,
            ]
            if combined_bounds
            else None
        ),
        "default_crs": default_crs,
        "raster_levels": raster_color_levels,
        "properties": combined_properties,
        "image_urls": image_urls,
        "tooltip": tool_tip,
    }


def export_map_service(image, form_data):
    try:
        output_format = form_data.get("export_format")
        output_path = form_data.get("export_path")
        output_filename = form_data.get("export_filename")
        file_paths = map(
            lambda x: safe_join(Config.PATHFILE, x),
            json.loads(form_data.get("file_paths")),
        )

        export_dir = safe_join(Config.PATHFILE_EXPORT, output_path)
        os.makedirs(export_dir, exist_ok=True)
        image_path = os.path.join(export_dir, f"{output_filename}.{output_format}")

        # Export image formats
        if image:
            img = Image.open(image)
            img.convert("RGB").save(image_path, output_format.upper(), quality=95)

        # Export shapefiles or raster datasets as images
        exported_images = [image_path]
        fig, ax = plt.subplots(figsize=(10, 8))
        raster_data = None

        for file_path in file_paths:
            fig, ax = plt.subplots(figsize=(10, 8))  # Create a new figure for each file

            if file_path.endswith(".shp"):
                gdf = gpd.read_file(file_path)
                gdf.plot(ax=ax, edgecolor="black")
            elif file_path.endswith(".tif") or file_path.endswith(".tiff"):
                dataset = gdal.Open(file_path)
                band = dataset.GetRasterBand(1)
                cmap = get_metadata_colormap(band)
                raster_data, _, raster_min, raster_max = get_raster_normalized(band)
                # Normalize raster values
                norm = mcolors.Normalize(vmin=raster_min, vmax=raster_max)
                # Display raster
                ax.imshow(raster_data, cmap=cmap, norm=norm, alpha=1)
                # Add raster legend (Colorbar)
                cbar = plt.colorbar(
                    plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                    ax=ax,
                    fraction=0.03,
                    pad=0.04,
                )
                cbar.set_label("Raster Classification", fontsize=12)

            # Add north arrow
            ax.annotate(
                "N",
                xy=(0.05, 0.9),
                xycoords="axes fraction",
                fontsize=14,
                fontweight="bold",
                ha="center",
            )
            ax.arrow(
                0.05,
                0.75,
                0,
                0.1,
                transform=ax.transAxes,
                color="black",
                head_width=0.02,
                head_length=0.03,
                lw=2,
            )

            # Save plot
            file_name = os.path.basename(file_path).split(".")[0]
            image_path = os.path.join(
                export_dir, f"{output_filename}_{file_name}.{output_format}"
            )
            plt.savefig(image_path, dpi=300, format=output_format)
            plt.close(fig)

            exported_images.append(image_path)

        # Combine exported images into a single zip file
        zip_path = os.path.join(export_dir, f"{output_filename}.zip")
        with ZipFile(zip_path, "w") as zipf:
            for image_path in exported_images:
                zipf.write(image_path, os.path.basename(image_path))

        return {"file_path": zip_path}
    except Exception as e:
        return {"error": str(e)}
