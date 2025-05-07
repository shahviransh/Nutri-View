from flask import jsonify, request, send_file
import mimetypes
from werkzeug.utils import safe_join
import os
import sys
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt,
    verify_jwt_in_request,
)
from dotenv import load_dotenv
import secrets
import bcrypt
from config import Config
from services import (
    fetch_data_service,
    get_files_and_folders,
    get_table_names,
    export_data_service,
    get_multi_columns_and_time_range,
    process_geospatial_data,
    export_map_service,
    fetch_geojson_colors,
)
from utils import shutdown_server, clear_cache
from validate import (
    validate_get_data_args,
    validate_export_data_args,
    validate_get_tables_args,
    validate_list_files_args,
    validate_get_table_details_args,
    validate_geospatial_args,
    validate_export_map_args,
    validate_serve_tif_args,
)

# Load environment variables
load_dotenv()

# In the Tauri EXE sidecar, HTTPS is not required and we can use default credentials.
# When running as a web app, HTTPS is required and proper environment variables should be set for security.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "default")
ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD", bcrypt.hashpw("default".encode(), bcrypt.gensalt()).decode()
)
JWT_SECRET_KEY = secrets.token_hex(256)

# Store revoked tokens
revoked_tokens = set()


def register_routes(app, cache):
    app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour
    jwt = JWTManager(app)

    @app.route("/api/login", methods=["POST"])
    def login():
        """
        Authenticate user using hashed password.
        """
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        # Verify username and hashed password
        if username != ADMIN_USERNAME or not bcrypt.checkpw(
            password.encode(), ADMIN_PASSWORD.encode()
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        access_token = create_access_token(identity=username)

        return jsonify(access_token=access_token)

    @app.route("/api/logout", methods=["POST"])
    @jwt_required()
    def logout():
        """
        Logout the user by revoking the token.
        """
        jti = get_jwt()["jti"]  # Get the unique identifier of the token
        revoked_tokens.add(jti)
        return jsonify({"message": "Logged out successfully"}), 200

    # Token revocation check
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload["jti"] in revoked_tokens

    @app.route("/api/verify-token", methods=["GET"])
    def verify_token():
        """
        Verify the JWT token in the request headers.
        """
        try:
            verify_jwt_in_request()
            return jsonify({"valid": True}), 200
        except:
            return jsonify({"valid": False}), 401

    @app.route("/api/upload_folder", methods=["POST"])
    @jwt_required()
    def upload_folder():
        """
        Endpoint to upload a folder with files to the server.
        """
        # The form data sent from the frontend
        files = request.files.getlist("files")  # This retrieves all files

        if not files:
            return jsonify({"error": "No files uploaded"})

        # Loop through each file and save it in the corresponding folder
        for file in files:
            file_path = safe_join(Config.PATHFILE, file.filename)

            # Ensure the file is not already there checking for duplicates
            if (
                os.path.exists(file_path)
                and os.path.getsize(file_path) == file.content_length
            ):
                continue

            # Get the folder name from the file's filename
            folder_name = os.path.dirname(file_path)
            os.makedirs(folder_name, exist_ok=True)
            file.save(file_path)

        return (
            jsonify({"message": "Files uploaded successfully"}),
            200,
        )

    @app.route("/api/get_data", methods=["GET"])
    @jwt_required()
    @cache.cached(timeout=300, query_string=True)
    def get_data():
        data = request.args

        # Validate the request arguments
        validation_response = validate_get_data_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        response = fetch_data_service(data)

        return jsonify(response)

    @app.route("/api/export_data", methods=["GET", "POST"])
    # This endpoint is not cached because the file is generated dynamically
    @jwt_required()
    def export_data():
        data = request.args if request.method == "GET" else request.json
        validation_response = validate_export_data_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        if request.method == "POST":
            if data.get("date_type", None):
                is_empty = False
            else:
                is_empty = True
                data["date_type"] = "GeoJson Only"
            file_path = export_data_service(data, is_empty)
        else:
            file_path = export_data_service(data)

        if file_path.get("error", None):
            return jsonify(file_path)

        # Determine the mimetype based on the file extension
        file_extension = file_path.get("file_path").split(".")[-1].lower()
        mimetype = (
            mimetypes.types_map.get(f".{file_extension}", "application/octet-stream")
            if file_extension != "xlsx"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        return send_file(
            file_path.get("file_path"), mimetype=mimetype, as_attachment=True
        )

    @app.route("/api/get_tables", methods=["GET"])
    @jwt_required()
    @cache.cached(timeout=300, query_string=True)
    def get_tables():
        data = request.args

        # Validate the request arguments
        validation_response = validate_get_tables_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        # Fetch the table names from the database
        tables = get_table_names(data)

        return jsonify(tables.get("tables"))

    @app.route("/api/list_files", methods=["GET"])
    @jwt_required()
    def list_files():
        """
        Endpoint to list all files and directories in the specified path.
        """
        data = request.args

        # Validate the request arguments
        validation_response = validate_list_files_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        files_and_folders = get_files_and_folders(data)

        return jsonify(files_and_folders.get("files_and_folders"))

    @app.route("/api/get_table_details", methods=["GET"])
    @jwt_required()
    @cache.cached(
        timeout=300, query_string=True
    )  # Cache this endpoint for 2 minutes (120 seconds)
    def get_table_details():
        """
        Endpoint to get table column names, time start, time end, and ID list, date type, and default interval.
        """
        data = request.args

        # Validate the request arguments
        validation_response = validate_get_table_details_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        columns_and_time_range_dict = get_multi_columns_and_time_range(data)

        return jsonify(columns_and_time_range_dict)

    @app.route("/api/geospatial", methods=["GET"])
    @jwt_required()
    @cache.cached(timeout=300, query_string=True)
    def geospatial():
        """
        API endpoint to return GeoJSON/Tiff Image Url, bounds, and center.
        """
        data = request.args

        # Validate the request arguments
        validation_response = validate_geospatial_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        geo_data = process_geospatial_data(data)

        return jsonify(geo_data)

    @app.route("/api/geotiff/<path:filename>", methods=["GET"])
    @jwt_required()
    def serve_tif(filename):
        """
        Serve the TIF file from the specified path.
        """
        # Ensure the file has a .tif or .tiff extension
        if not (filename.lower().endswith((".tif", ".tiff", ".png"))):
            return jsonify({"error": "Only .tif or .tiff files are allowed"})
        
        # Ensure the file is in the TEMP directory
        filename = safe_join(Config.TEMPDIR, filename)

        # Validate the file path
        validation_response = validate_serve_tif_args(filename)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        return send_file(filename, mimetype="image/png", as_attachment=True)

    @app.route("/api/get_geojson_colors", methods=["GET"])
    @jwt_required()
    @cache.cached(timeout=300, query_string=True)
    def get_geojson_colors():
        """
        API endpoint to get GeoJSON colors.
        """
        data = request.args

        # Validate the request arguments
        validation_response = validate_get_data_args(data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        colors = fetch_geojson_colors(data)

        return jsonify(colors)

    @app.route("/api/export_map", methods=["POST"])
    @jwt_required()
    def export_map():
        """
        API endpoint to export the map image.
        """
        image = request.files.get("image")
        form_data = request.form.to_dict()

        # Validate the request arguments
        validation_response = validate_export_map_args(image, form_data)
        if validation_response.get("error", None):
            return jsonify(validation_response)

        file_path = export_map_service(image, form_data)

        if file_path.get("error", None):
            return jsonify(file_path)

        mimetype = mimetypes.types_map.get(".zip", "application/octet-stream")

        return send_file(
            file_path.get("file_path"), mimetype=mimetype, as_attachment=True
        )

    @app.route("/api/health", methods=["GET"])
    def health():
        return "Server is running...", 200

    @app.route("/api/shutdown", methods=["GET"])
    def shutdown():
        # Shutdown the server if running as a standalone executable
        if getattr(sys, "frozen", False):
            shutdown_server()
            return "Server shutting down...", 200
        else:
            return "Server is not running as a standalone executable.", 200

    @app.route("/api/clear_cache", methods=["GET"])
    def clear_cache_route():
        clear_cache(cache)
        return "Cache cleared.", 200
