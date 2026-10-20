"""Playbooks entrypoint. Developed by: Marc Bteich."""
from common.app_factory import create_service_app, run_service
from database.migrate import upgrade_action_history
from services.playbooks.routes import playbooks_bp

app=create_service_app('playbooks',playbooks_bp)
with app.app_context():
    upgrade_action_history()
if __name__=='__main__':
    run_service(app)
