"""Non-destructive upgrade for Marc's action-history column. Developed by: Marc Bteich."""
from common.db import db
from sqlalchemy import inspect, text


def upgrade_action_history():
    """Run in an app context before using a pre-Playbooks development database."""
    inspector = inspect(db.engine)
    if 'response_actions' in inspector.get_table_names():
        columns = {c['name'] for c in inspector.get_columns('response_actions')}
        if 'execution_history' not in columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE response_actions ADD COLUMN execution_history JSON NOT NULL DEFAULT '[]'"))
