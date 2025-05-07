from cerberus import Validator
import re
import os
from config import Config


def validate_request_args(schema, request_args):
    """
    Validates the request arguments using Cerberus and applies additional security checks.
    """
    validator = Validator(schema)
    data = {key: request_args.get(key) for key in schema.keys() if key in request_args}

    if not validator.validate(data):
        return {
            "error": f"Invalid parameters: {getUserValidationError(validator.errors)}"
        }

    # Additional security checks for path traversal and SQL injection
    for key, value in data.items():
        if isinstance(value, str):
            # Check for path traversal
            if re.search(r"(\.\.\/|\.\.\\)", value):
                return {
                    "error": f"Potential path traversal detected in parameter: {key}"
                }

            # Check for SQL injection patterns
            if re.search(
                r"(\bSELECT\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bDROP\b|;|--|\bEXEC\b|\bUNION\b)",
                value,
                re.IGNORECASE,
            ):
                return {
                    "error": f"Potential SQL injection detected in parameter: {key}"
                }

    return validator.document


# Usage for the /api/get_data endpoint
def validate_get_data_args(request_args):
    schema = {
        "db_tables": {"type": "string", "required": True},
        "columns": {"type": "string", "required": True},
        "id": {
            "type": "string",
            "required": True,
            "regex": r'\["\d+"(,\s*"\d+")*\]|\[\]',
        },
        "id_column": {
            "type": "string",
            "required": True,
            "regex": r"^\s*|[\w\s-]+$",
        },
        "start_date": {
            "type": "string",
            "required": True,
            "regex": r"^\d*|^\d{4}-\d{2}-\d{2}$|^$",
        },
        "end_date": {
            "type": "string",
            "required": True,
            "regex": r"^\d*|^\d{4}-\d{2}-\d{2}$|^$"
        },
        "date_type": {
            "type": "string",
            "required": True,
            "allowed": ["Time", "Date", "Month", "Year", ""],
        },
        "interval": {
            "type": "string",
            "required": True,
            "default": "daily",
            "regex": r"^[a-zA-Z]+$",
        },
        "method": {"type": "string", "required": True, "default": "['Equal']"},
        "statistics": {"type": "string", "required": True, "default": "['None']"},
        "month": {
            "type": "string",
            "required": False,
            "allowed": [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "",
            ],
        },
        "season": {
            "type": "string",
            "required": False,
            "allowed": ["summer", "winter", "fall", "spring", ""],
        },
        "feature": {
            "type": "string",
            "required": False,
        },
        "feature_statistic": {
            "type": "string",
            "required": False,
            "allowed": ["mean", "sum", "max", "min"],
        },
        "spatial_scale": {
            "type": "string",
            "required": False,
            "allowed": ["subarea", "field", "reach", "subbasin", "unknown"]
        },
        "math_formula": {
            "type": "string",
            "required": False,
        },
    }
    return validate_request_args(schema, request_args)


# Usage for the /api/export_data endpoint
def validate_export_data_args(request_args):
    schema = {
        "db_tables": {"type": "string", "required": True},
        "columns": {"type": "string", "required": True},
        "id": {
            "type": "string",
            "required": True,
            "regex": r'\["\d+"(,\s*"\d+")*\]|\[\]',
        },
        "id_column": {
            "type": "string",
            "required": True,
            "regex": r"^\s*|[\w\s-]+$",
        },
        "start_date": {
            "type": "string",
            "required": True,
            "regex": r"^\d*|^\d{4}-\d{2}-\d{2}$|^$",
        },
        "end_date": {
            "type": "string",
            "required": True,
            "regex": r"^\d*|^\d{4}-\d{2}-\d{2}$|^$",
        },
        "date_type": {
            "type": "string",
            "required": True,
            "allowed": ["Time", "Date", "Month", "Year", ""],
        },
        "interval": {
            "type": "string",
            "required": True,
            "default": "daily",
            "regex": r"^[a-zA-Z]+$",
        },
        "method": {"type": "string", "required": True, "default": "['Equal']"},
        "statistics": {"type": "string", "required": True, "default": "['None']"},
        "export_filename": {
            "type": "string",
            "required": True,
            "regex": r"^[\w,\s-]+$",
        },
        "export_format": {
            "type": "string",
            "required": True,
            "allowed": [
                "csv",
                "txt",
                "xlsx",
                "png",
                "jpg",
                "jpeg",
                "svg",
                "pdf",
                "shp",
            ],
        },
        "export_path": {"type": "string", "required": True},
        "options": {"type": "string", "required": True},
        "month": {
            "type": "string",
            "required": False,
            "allowed": [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "",
            ],
        },
        "season": {
            "type": "string",
            "required": False,
            "allowed": ["summer", "winter", "fall", "spring", ""],
        },
        "geojson_data": {
            "type": "string",
            "required": False,
        },
        "feature": {
            "type": "string",
            "required": False,
        },
        "feature_statistic": {
            "type": "string",
            "required": False,
            "allowed": ["mean", "sum", "max", "min"],
        },
        "spatial_scale": {
            "type": "string",
            "required": False,
            "allowed": ["subarea", "field", "reach", "subbasin", "unknown"]
        },
        "default_crs": {
            "type": "string",
            "required": False,
            "allowed": ["EPSG:4326", "EPSG:26917"],
        },
        "math_formula": {
            "type": "string",
            "required": False,
        },
    }
    return validate_request_args(schema, request_args)


# Usage for the /api/get_tables endpoint
def validate_get_tables_args(request_args):
    schema = {"db_path": {"type": "string", "required": True}}
    return validate_request_args(schema, request_args)


# Usage for /api/list_files endpoint
def validate_list_files_args(request_args):
    schema = {"folder_path": {"type": "string", "required": True}}
    return validate_request_args(schema, request_args)


# Usage for /api/get_table_details endpoint
def validate_get_table_details_args(request_args):
    schema = {"db_tables": {"type": "string", "required": True}}
    return validate_request_args(schema, request_args)


# Usage for /api/geospatial endpoint
def validate_geospatial_args(request_args):
    schema = {"file_paths": {"type": "string", "required": True}}
    return validate_request_args(schema, request_args)


# Usage for /api/export_map endpoint
def validate_export_map_args(image, form_data):
    if not image.mimetype.startswith("image/"):
        return {"error": "Invalid image file format"}
    schema = {
        "export_format": {
            "type": "string",
            "required": True,
            "allowed": ["png", "jpg", "jpeg", "pdf"],
        },
        "export_path": {"type": "string", "required": True},
        "export_filename": {
            "type": "string",
            "required": True,
            "regex": r"^[\w,\s-]+$",
        },
    }
    return validate_request_args(schema, form_data)


def validate_serve_tif_args(filename):
    if filename and not os.path.exists(filename):
        return {"error": "Invalid path specified for the GeoTIFF file."}
    return {"filename": filename}


def getUserValidationError(errors):
    """
    Get user-friendly error messages from Cerberus validation errors.
    """
    # Mapping regex patterns to human-readable messages
    regex_messages = {
        r"^\d*|^\d{4}-\d{2}-\d{2}$|^$": "should be in the format YYYY-MM-DD (e.g., 2024-01-20) or Day or Month or Year.",
        r"^\d+(\.\d+)?$": "should be a number (e.g., 123.45).",
        r"^[\w,\s-]+$$": "should contain only letters, numbers, spaces, commas, underscore and hyphens.",
        r"^\s*|[\w\s-]+$": "should contain only letters, numbers, spaces, underscores and hyphens.",
        r'\["\d+"(,\s*"\d+")*\]|\[\]': "should be a numbers quoted and enclosed in square brackets (e.g., ['1','2','3']).",
    }

    error_messages = []
    for field, error in errors.items():
        if isinstance(error, list):
            for e in error:
                if "does not match" in e:
                    # Check if the error is related to regex and map it
                    for pattern, message in regex_messages.items():
                        if pattern in e:
                            error_messages.append(f"{field}: {message}")
                            break
                    else:
                        error_messages.append(f"{field}: {e}")
                else:
                    error_messages.append(f"{field}: {e}")
        else:
            error_messages.append(f"{field}: {error}")

    return ", ".join(error_messages)
