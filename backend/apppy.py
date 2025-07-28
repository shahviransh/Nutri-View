from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from routes import register_routes
from error_handlers import register_error_handlers
from dotenv import load_dotenv
import os
import shutil
from config import Config

if os.path.exists(Config.TEMPDIR):
    shutil.rmtree(Config.TEMPDIR)

os.makedirs(Config.TEMPDIR, exist_ok=True)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure caching
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

# Register routes and error handlers
register_routes(app, cache)
register_error_handlers(app)

if __name__ == "__main__":
    if os.getenv("PRODUCTION") == "True":
        from waitress import serve

        os.environ["WAITRESS"] = "1"
        serve(app, host="127.0.0.1", port=5000)
    else:
        app.run(debug=True)
