"""Notification and Alert Management Service. Run from the repo root: python -m services.notifications.app"""
from common.app_factory import create_service_app, run_service
from services.notifications.routes import notifications_bp

app = create_service_app("notifications", notifications_bp)

if __name__ == "__main__":
    run_service(app)
