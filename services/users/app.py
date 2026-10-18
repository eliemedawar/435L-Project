"""Users and Identity Management Service. Run from the repo root: python -m services.users.app"""
from common.app_factory import create_service_app, run_service
from services.users.routes import users_bp

app = create_service_app("users", users_bp)

if __name__ == "__main__":
    run_service(app)
