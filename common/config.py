"""Central configuration, loaded from the .env file at the repository root."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
(ROOT_DIR / "database").mkdir(exist_ok=True)   # SQLite cannot create its file in a missing folder

# Port of every service. Other services find each other through these.
SERVICE_PORTS = {
    "users": 5001,
    "assets": 5002,
    "incidents": 5003,
    "threats": 5004,
    "logs": 5005,
    "reports": 5006,
    "vulnerabilities": 5007,
    "notifications": 5008,
    "playbooks": 5009,
}


def _required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name} in .env (copy .env.example to .env and fill it in)")
    return value


class Config:
    JWT_SECRET = _required("JWT_SECRET")
    SERVICE_KEY = _required("SERVICE_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))

    # One shared database for all services. The SQLite path is absolute so every
    # service process points to the same file no matter where it is started from.
    DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{(ROOT_DIR / 'database' / 'sidrms.db').as_posix()}"

    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "2"))


def service_url(service_name):
    """Base URL of a service, e.g. service_url('logs') -> 'http://127.0.0.1:5005'.
    Can be overridden in .env with LOGS_URL=..., USERS_URL=..., etc."""
    override = os.getenv(f"{service_name.upper()}_URL")
    if override:
        return override.rstrip("/")
    return f"http://127.0.0.1:{SERVICE_PORTS[service_name]}"
