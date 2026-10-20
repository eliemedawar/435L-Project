"""Run with python -m services.assets.app. Developed by: Marc Bteich."""
from common.app_factory import create_service_app, run_service
from services.assets.routes import assets_bp

app = create_service_app("assets", assets_bp)

if __name__ == "__main__":
    run_service(app)
