"""Role names used in tokens, the users table and @require_auth."""
ADMIN = "admin"        # Security Administrator
ANALYST = "analyst"    # Security Analyst
USER = "user"          # Regular Employee/User
AUDITOR = "auditor"    # Auditor (read-only)

ALL_ROLES = (ADMIN, ANALYST, USER, AUDITOR)
