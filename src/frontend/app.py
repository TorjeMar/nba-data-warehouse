"""Umbrella frontend for the Basketball Data Warehouse."""

from __future__ import annotations

from dotenv import load_dotenv
from flask import Flask

from src.frontend.backend.routes import register_routes


load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
