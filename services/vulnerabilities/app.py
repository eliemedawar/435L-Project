"""Vulnerability entrypoint. Developed by: Marc Bteich."""
from common.app_factory import create_service_app, run_service
from services.vulnerabilities.routes import vulnerabilities_bp

app = create_service_app('vulnerabilities', vulnerabilities_bp)
if __name__ == '__main__':
    run_service(app)
