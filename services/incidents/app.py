"""Incident Management Service. Run from the repo root: python -m services.incidents.app"""
from common.app_factory import create_service_app, run_service
from services.incidents.routes import incidents_bp

app = create_service_app("incidents", incidents_bp)

if __name__ == "__main__":
    run_service(app)
