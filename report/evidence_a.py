"""Evidence pages and screenshots for Elie Medawar's services, from genuine Newman records.
Developed by: Elie Medawar. Uses the same page style as Marc's report/generate.py and
captures each page with Microsoft Edge in headless mode.

    python report/evidence_a.py          (run after postman/execute_a.py)
"""
import html
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "report/evidence"
SHOTS = ROOT / "report/screenshots/elie"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
COLLECTIONS = ("users", "logs", "incidents", "notifications", "reports_a")
STYLE = ('<style>body{font:16px Arial;margin:32px;color:#172033;background:#f7f9fc}h1{font-size:24px}h2{font-size:19px}'
         'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;border:1px solid #cbd5e1;border-radius:6px;'
         'padding:16px;font:14px Consolas;line-height:1.45}small{color:#475569}article{max-width:1120px}</style>')

# (method, path regex) -> API title from the brief
API_TITLES = [
    ("POST", r"^/users/register$", "User Registration"), ("POST", r"^/users/login$", "User Login"),
    ("PUT", r"^/users/\d+$", "Update User Information"), ("DELETE", r"^/users/\d+$", "Delete User"),
    ("GET", r"^/users$", "Retrieve All Users"), ("GET", r"^/users/[^/]+$", "Retrieve User By Username"),
    ("POST", r"^/logs$", "Create Log Record"), ("GET", r"^/logs$", "Retrieve All Logs"),
    ("GET", r"^/logs/search$", "Search Logs"), ("GET", r"^/logs/user/\d+$", "Retrieve Logs By User"),
    ("GET", r"^/logs/\d+$", "Retrieve Specific Log"), ("DELETE", r"^/logs/\d+$", "Delete Logs"),
    ("PUT", r"^/logs/\d+$", "Update Log (immutability check)"),
    ("POST", r"^/incidents$", "Create Incident"), ("GET", r"^/incidents$", "Retrieve All Incidents"),
    ("GET", r"^/incidents/\d+$", "Retrieve Specific Incident"), ("PUT", r"^/incidents/\d+/assign$", "Assign Incident to Analyst"),
    ("PUT", r"^/incidents/\d+/status$", "Update Incident Status"), ("POST", r"^/incidents/\d+/notes$", "Add Investigation Notes"),
    ("POST", r"^/notifications$", "Create Notification"), ("GET", r"^/notifications/user/\d+$", "Retrieve User Notifications"),
    ("GET", r"^/notifications/search$", "Search Notifications"), ("GET", r"^/notifications/\d+$", "Retrieve Specific Notification"),
    ("PUT", r"^/notifications/\d+/read$", "Mark Notification as Read"), ("DELETE", r"^/notifications/\d+$", "Delete Notification"),
    ("GET", r"^/reports/summary$", "Generate Security Summary Report"), ("GET", r"^/reports/incidents$", "Generate Incident Report"),
    ("GET", r"^/reports/activity$", "Generate Activity Report"),
]


def api_title(method, path):
    for m, pattern, title in API_TITLES:
        if m == method and re.match(pattern, path):
            return title
    return f"{method} {path}"


def capture(page, png, height=2400):
    """Screenshot an HTML file with headless Edge, then trim the empty background below the content."""
    # A separate profile stops headless Edge from handing the job to an Edge window that is already open.
    # The previous headless run can hold that profile for a moment, so retry until the file appears.
    png.unlink(missing_ok=True)
    for attempt in range(8):
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                        f"--user-data-dir={ROOT / '.local/edge-profile'}", "--force-device-scale-factor=1",
                        f"--window-size=1200,{height}", f"--screenshot={png}", page.as_uri()],
                       capture_output=True, timeout=60)
        if png.exists():
            break
        time.sleep(1 + attempt)
    else:
        raise RuntimeError(f"Edge did not produce {png.name}")
    with Image.open(png) as image:
        rgb = image.convert("RGB")
        width, total = rgb.size
        background = rgb.getpixel((width - 5, total - 5))
        bottom = total
        while bottom > 50 and all(rgb.getpixel((x, bottom - 1)) == background for x in range(0, width, 7)):
            bottom -= 1
        rgb.crop((0, 0, width, min(total, bottom + 24))).save(png)


def request_pages():
    cards = []
    for collection in COLLECTIONS:
        result = json.loads((EVIDENCE / f"newman-{collection}.json").read_text(encoding="utf-8"))
        for number, record in enumerate(result["records"], 1):
            path = urlparse(record["url"]).path
            if collection != "users" and path == "/users/login":
                continue          # setup logins of the other collections; login evidence comes from the Users run
            title = api_title(record["method"], path)
            caption = f"Elie Medawar – {title} – {record['name']} (HTTP {record['status']})"
            name = f"newman-{collection}-{number:02}"
            page = EVIDENCE / f"{name}.html"
            page.write_text("\n".join([
                '<!doctype html><meta charset="utf-8">', STYLE, "<article>",
                "<h1>" + html.escape(caption) + "</h1>",
                "<small>Genuine Newman execution report • " + html.escape(result["executed_at"]) + " • source: newman-"
                + collection + ".json</small>",
                "<p>" + html.escape(record["method"] + " " + record["url"]) + "</p>",
                "<h2>Actual request body (credentials redacted)</h2><pre>" + html.escape(json.dumps(record["request"], indent=2)) + "</pre>",
                "<h2>Actual response — HTTP " + str(record["status"]) + "</h2><pre>"
                + html.escape(json.dumps(record["response"], indent=2)) + "</pre>",
                "<p>This screenshot displays stored results from an actual API execution. It is not a simulated API response "
                "or a Postman GUI screenshot.</p></article>"]), encoding="utf-8")
            cards.append(dict(name=name, collection=collection, title=title, request=record["name"], caption=caption,
                              method=record["method"], path=path, status=record["status"]))
    return cards


def database_page():
    connection = sqlite3.connect(ROOT / ".local/evidence_a.db")
    parts = ['<!doctype html><meta charset="utf-8">', STYLE,
             "<h1>Elie Medawar – Database records – users, incidents, investigation_notes, logs, notifications "
             "(actual SQLite after the Newman run)</h1>"]
    for table, columns, limit in (
            ("users", "id, full_name, username, email, department, role, account_status, created_at, last_login", 10),
            ("incidents", "id, title, category, severity, reporter_id, asset_id, assigned_analyst_id, status, created_at, resolved_at", 10),
            ("investigation_notes", "id, incident_id, analyst_id, content, created_at", 10),
            ("notifications", "id, user_id, title, notification_type, severity, status, created_at, read_at", 10),
            ("logs", "id, user_id, username, action, severity, related_service, timestamp", 12)):
        rows = connection.execute(f"SELECT {columns} FROM {table} ORDER BY id LIMIT {limit}").fetchall()
        names = [c.strip() for c in columns.split(",")]
        total = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        parts.append(f"<h2>{table} ({total} rows, first {len(rows)} shown)</h2><pre>"
                     + html.escape(json.dumps([dict(zip(names, r)) for r in rows], indent=2, default=str)) + "</pre>")
    hashes = connection.execute("SELECT username, substr(password_hash, 1, 7) || '…' FROM users ORDER BY id").fetchall()
    parts.append("<h2>Password storage: bcrypt hashes only (prefix shown)</h2><pre>"
                 + html.escape(json.dumps(dict(hashes), indent=2)) + "</pre>")
    page = EVIDENCE / "database-inspection-elie.html"
    page.write_text("\n".join(parts), encoding="utf-8")
    return page


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    cards = request_pages()
    for card in cards:
        capture(EVIDENCE / f"{card['name']}.html", SHOTS / f"{card['name']}.png")
    capture(database_page(), SHOTS / "database-inspection-elie.png", height=6000)
    (EVIDENCE / "screenshot-manifest-elie.json").write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")
    print(f"{len(cards)} request screenshots + database screenshot in {SHOTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
