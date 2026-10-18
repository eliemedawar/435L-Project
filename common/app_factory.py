"""Builds every service's Flask app the same way.

    app = create_service_app("assets", assets_bp)
    if __name__ == "__main__":
        run_service(app)
"""
from flask import Flask

import models  # noqa: F401  (importing the package registers every table)
from common.config import SERVICE_PORTS, Config
from common.db import db
from common.errors import register_error_handlers


def _create_tables():
    """Create missing tables only (never alters or drops). Placeholder tables, declared just so a
    foreign key can point at a teammate's table that is not merged yet, are never created."""
    tables = [t for t in db.metadata.sorted_tables if not t.info.get("placeholder")]
    db.metadata.create_all(bind=db.engine, tables=tables)


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
        _create_tables()
    return app


def init_database():
    """Create all tables once, before several services start at the same time (used by run_all.py)."""
    app = Flask("init_database")
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
    db.init_app(app)
    with app.app_context():
        _create_tables()


def run_service(app):
    port = SERVICE_PORTS[app.config["SERVICE_NAME"]]
    # threaded=True so a service can handle a request that calls back into itself (e.g. logs)
    app.run(host="127.0.0.1", port=port, debug=Config.DEBUG, threaded=True)
