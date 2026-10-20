"""Run Elie Medawar's Postman collections with Newman against the nine live services.
Developed by: Elie Medawar. Same approach as Marc's postman/execute.py: a fresh, isolated
SQLite database, private generated passwords, and only redacted records saved as evidence.

    python postman/execute_a.py

Needs Node.js and Newman installed under .local/tooling (see report/TOOLS.md).
A copy of the database after the run is kept in .local/evidence_a.db for the
database screenshots.
"""
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import sys
import time

import requests

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = ("users", "logs", "incidents", "notifications", "reports_a")   # order matters: Users creates the accounts
SERVICES = ("users", "assets", "incidents", "threats", "logs", "reports", "vulnerabilities", "notifications", "playbooks")


def wait_for_services():
    for port in range(5001, 5010):
        deadline = time.monotonic() + 30
        while True:
            try:
                if requests.get(f"http://127.0.0.1:{port}/", timeout=1).status_code == 404:
                    break
            except requests.ConnectionError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError(f"Service on port {port} did not start")
            time.sleep(0.2)


def create_admin(env, password):
    code = (
        "import os\n"
        "from common.app_factory import create_service_app\n"
        "from common.db import db\n"
        "from models.users import User\n"
        "app = create_service_app('users')\n"
        "with app.app_context():\n"
        "    user = User(username='admin', full_name='Elie Medawar', email='admin@corp.com', department='Security', role='admin')\n"
        "    user.set_password(os.environ['LOCAL_TEST_PASSWORD'])\n"
        "    db.session.add(user); db.session.commit()\n"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=dict(env, LOCAL_TEST_PASSWORD=password),
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr)


def create_lab_assets(admin_password):
    """Incidents must reference an existing asset, so create three through Marc's Assets API."""
    token = requests.post("http://127.0.0.1:5001/users/login",
                          json={"username": "admin", "password": admin_password}, timeout=10).json()["data"]["token"]
    for name, kind, ip, criticality in (("Web Server", "Server", "10.0.0.10", "Critical"),
                                        ("HR Database", "Database", "10.0.0.20", "High"),
                                        ("Finance Laptop", "Workstation", "10.0.1.5", "Medium")):
        response = requests.post("http://127.0.0.1:5002/assets", headers={"Authorization": f"Bearer {token}"}, timeout=10,
                                 json={"asset_name": name, "asset_type": kind, "ip_address": ip, "owner_id": 1,
                                       "department": "IT", "criticality": criticality})
        response.raise_for_status()


def main():
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    work = local / "run_a"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    dbfile = work / "runtime.db"
    env = dict(os.environ, DATABASE_URL="sqlite:///" + dbfile.as_posix(), JWT_SECRET=secrets.token_hex(32),
               SERVICE_KEY=secrets.token_hex(32), FLASK_DEBUG="0")
    with closing(sqlite3.connect(dbfile)) as connection:
        connection.executescript((ROOT / "database/schema.sql").read_text())

    passwords = {role: secrets.token_urlsafe(18) + "Aa!1" for role in ("admin", "analyst", "auditor", "user")}
    create_admin(env, passwords["admin"])
    runtime = dict(admin_username="admin", analyst_username="lara", auditor_username="nadia", user_username="rami")
    runtime.update({role + "_password": value for role, value in passwords.items()})
    private = work / "environment.json"
    private.write_text(json.dumps(runtime))

    processes, failures = [], []
    with (work / "services.log").open("w") as log:
        try:
            for name in SERVICES:
                processes.append(subprocess.Popen([sys.executable, "-m", f"services.{name}.app"], cwd=ROOT, env=env,
                                                  stdout=log, stderr=log,
                                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))
            wait_for_services()
            create_lab_assets(passwords["admin"])
            for name in COLLECTIONS:
                result = subprocess.run(["node", str(ROOT / "postman/run_collection.cjs"),
                                         str(ROOT / f"postman/{name}.postman_collection.json"), str(private),
                                         f"newman-{name}"], cwd=ROOT, capture_output=True, text=True, timeout=300)
                print(result.stdout)
                if result.returncode:
                    failures.append(name)
                    print(result.stderr)
            with closing(sqlite3.connect(dbfile)) as connection:
                assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
                assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            for process in processes:
                process.terminate()
            for process in processes:
                process.wait(timeout=15)
    shutil.copy(dbfile, local / "evidence_a.db")
    private.unlink()
    if failures:
        raise SystemExit("Postman assertions failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
