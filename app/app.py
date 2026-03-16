from pathlib import Path
import os

from flask import Flask
from dotenv import load_dotenv

from .routes import register_routes


def create_app():
    project_root = Path(__file__).resolve().parent.parent  # .../Snip-Snap
    load_dotenv(project_root / ".env")  # .../Snip-Snap/.env

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    from .api import api_bp
    app.register_blueprint(api_bp)

    @app.after_request
    def add_cache_headers(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Service-Worker-Allowed"] = "/"
        return response

    register_routes(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)