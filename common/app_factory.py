"""Builds every service's Flask app the same way.

    app = create_service_app("assets", assets_bp)
    if __name__ == "__main__":
        run_service(app)
"""
import importlib
import pkgutil

from flask import Flask

import models
from common.config import SERVICE_PORTS, Config
from common.db import db
from common.errors import register_error_handlers


def _import_all_models():
    """Import every module in models/ so all tables (and their foreign keys) are known to SQLAlchemy."""
    for module in pkgutil.iter_modules(models.__path__):
        importlib.import_module(f"models.{module.name}")


def create_service_app(service_name, *blueprints):
    app = Flask(service_name)
    app.config["SERVICE_NAME"] = service_name
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
    app.json.sort_keys = False

    db.init_app(app)
    register_error_handlers(app)
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    with app.app_context():
        _import_all_models()
        db.create_all()   # creates missing tables only, never alters or drops existing ones
    return app


def run_service(app):
    port = SERVICE_PORTS[app.config["SERVICE_NAME"]]
    # threaded=True so a service can handle a request that calls back into itself (e.g. logs)
    app.run(host="127.0.0.1", port=port, debug=Config.DEBUG, threaded=True)
