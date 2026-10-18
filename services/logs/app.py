"""Security Audit Logging Service. Run from the repo root: python -m services.logs.app"""
from common.app_factory import create_service_app, run_service
from services.logs.routes import logs_bp

app = create_service_app("logs", logs_bp)

if __name__ == "__main__":
    run_service(app)
