"""Users table. Owner: Elie Medawar."""
import bcrypt

from common.db import db, iso, utcnow
from common.enums import ACCOUNT_STATUSES
from common.roles import ALL_ROLES


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(60), nullable=False)    # bcrypt hash, never the plain password
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    account_status = db.Column(db.String(20), nullable=False, default="Active")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login = db.Column(db.DateTime)                          # user activity information

    __table_args__ = (
        db.CheckConstraint(f"role IN {ALL_ROLES}", name="ck_users_role"),
        db.CheckConstraint(f"account_status IN {ACCOUNT_STATUSES}", name="ck_users_account_status"),
    )

    def set_password(self, plain_password):
        self.password_hash = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, plain_password):
        return bcrypt.checkpw(plain_password.encode(), self.password_hash.encode())

    @property
    def can_authenticate(self):
        return self.account_status == "Active"

    def to_dict(self):
        """Public representation. The password hash is never returned."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "department": self.department,
            "role": self.role,
            "account_status": self.account_status,
            "created_at": iso(self.created_at),
            "last_login": iso(self.last_login),
        }
