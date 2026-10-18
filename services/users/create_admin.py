"""Create the first Security Administrator (nobody can register as admin through the API without one).

    python -m services.users.create_admin --username admin --email admin@corp.com --full-name "Elie Medawar" --department "Security"

The password is asked interactively and is never shown or stored in plain text.
"""
import argparse
import getpass

from common.db import db
from common.errors import APIError
from common.roles import ADMIN
from models.users import User
from services.users.app import app
from services.users.service import PasswordValidator, UserService


def main():
    parser = argparse.ArgumentParser(description="Create a Security Administrator account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--department", default="Security Operations")
    args = parser.parse_args()

    password = getpass.getpass("Admin password: ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")

    with app.app_context():
        try:
            PasswordValidator.validate(password)
            UserService._ensure_unique(username=args.username, email=args.email.lower())
        except APIError as err:
            raise SystemExit(f"Error: {err.message}")
        user = User(full_name=args.full_name, username=args.username, email=args.email.lower(),
                    department=args.department, role=ADMIN)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Admin '{user.username}' created with id {user.id}")


if __name__ == "__main__":
    main()
