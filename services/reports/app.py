"""Combined Reports entrypoint. Developed by: Marc Bteich."""
from common.app_factory import create_service_app, run_service
from services.reports.routes_a import reports_a_bp
from services.reports.routes_b import reports_b_bp

app=create_service_app('reports',reports_a_bp,reports_b_bp)
if __name__=='__main__':
    run_service(app)
