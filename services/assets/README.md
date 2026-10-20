# Service 2 — Assets (Marc Bteich)

This service manages organizational assets on port **5002**. It uses Elie's shared
JWT authentication, role checks, JSON responses, SQLAlchemy database connection,
error handler, and HTTP audit helper. No shared files were changed.

## Run locally

Open PowerShell in the repository root. The virtual environment and private `.env`
have already been configured on Marc's machine. On a new machine:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

For a new installation, replace both placeholder secrets in `.env` with separate
random values generated using `python -c "import secrets; print(secrets.token_hex(32))"`.
Keep `DATABASE_URL` empty for SQLite. Keep `.env`, passwords, and JWTs private.
The teammates must share matching secrets when their services run together.

The development database has already been initialized on Marc's machine with all
ten tables and labelled sample accounts/data from database.seed. On a fresh clone, before starting any services,
initialize the full schema once with the following command. It refuses to overwrite
an existing database:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; import sqlite3; p=Path('database/sidrms.db'); assert not p.exists(), 'Database already exists: do not overwrite it'; c=sqlite3.connect(p); c.executescript(Path('database/schema.sql').read_text()); c.close(); print('Created all ten tables')"
```

`schema.sql` targets **SQLite development**, as permitted by the plan. It is not a
MySQL import script. All Person B services and models are now implemented. The
seed script provisions labelled samples and random private account passwords in
`.local/seed-credentials.json`, which is excluded from Git.

On this machine, the database and accounts have already been configured. For a
fresh development installation, run `python -m database.seed`, then `python run_all.py`
using the virtual environment. Seeding is additive and never resets an existing password.
The collections use admin, lara, nadia and rami; keep credentials private.

## Understand the implementation

- `models/assets.py`: the `Asset` class describes a database row and serializes it
  to JSON. The owner is a required foreign key to `users.id`.
- `service.py`: `AssetValidator` checks input before saving. `AssetService` makes
  ORM queries, verifies owners by HTTP, saves changes and requests audit events.
- `routes.py`: the eight routes check access and call the service class. Each route
  carries Marc's attribution comment. Internal routes require `X-Service-Key`.
- `app.py`: uses the existing factory so ports, database configuration and errors
  behave consistently with Elie's services.

`asset_type` is one of `Server`, `Workstation`, `Database`, `Application`,
`Network Device`, `Cloud Resource`, based on the brief's examples. `criticality`
is `Low`, `Medium`, `High`, or `Critical`. `status` is `Active`, `Inactive`, or
`Under Maintenance` and defaults to `Active`. IPs are validated and normalized
using Python's `ipaddress` module, supporting IPv4 and IPv6. Optional operating
system and location may be omitted or null. Empty bodies, wrong types, unknown
fields and invalid values return 400.

Example create body (replace owner_id with a real user ID):

```json
{
  "asset_name": "Security Lab Server",
  "asset_type": "Server",
  "ip_address": "192.0.2.10",
  "owner_id": 1,
  "department": "Security",
  "criticality": "Critical"
}
```

| Method and route | Roles / input |
|---|---|
| POST `/assets` | Admin. Requires name, type, IP, owner, department and criticality. Returns 201. |
| PUT `/assets/{id}` | Admin. Updates any provided name, owner, department, criticality or status. |
| DELETE `/assets/{id}` | Admin. Returns 200 with null data. |
| GET `/assets` | Admin, Auditor. Returns `{count, assets}`. |
| GET `/assets/{id}` | Admin, Analyst, Auditor. Returns one asset. |
| GET `/assets/search` | Admin, Analyst, Auditor. Returns `{count, assets}`. |
| GET `/internal/stats` | Service key only. Returns `total_assets`, `critical_assets`, `by_type`. |
| GET `/internal/assets/{id}` | Service key only. Required by Elie's Incidents service. |

Regular users have no access. JWTs use `Authorization: Bearer <token>`. A valid
service key is accepted only on internal endpoints, not public Assets APIs.
All responses use `{status, message, data}` for success and `{status, message}`
for errors. Missing/invalid/expired credentials return 401, insufficient role 403,
missing asset 404, and database constraint conflicts 409.

Search query keys are `name`, `type`, `ip`, `department`, `criticality`. Name and
department use case-insensitive literal substring matching; type, normalized IP,
and criticality use exact matching. Filters combine with AND. For example:
`/assets/search?type=Server&criticality=Critical`. At least one nonempty filter is
required. Unknown or repeated filter keys are rejected. No matches return an
empty list with 200. ORM parameter binding prevents input from becoming SQL;
SQL LIKE wildcards in name/department searches are escaped.

An existing incident survives asset deletion with `asset_id` set to null, matching
Elie's FK. A vulnerability requires its asset, so it blocks deletion with 409.
Asset names and IPs are not unique: the brief does not require uniqueness.
Create/update/delete request `ASSET_CREATED`, `ASSET_UPDATED`, `ASSET_DELETED`
audit records after commit. Shared authentication logs role denials automatically.
Owner verification fails with 503 if Users is unavailable. The shared audit helper
deliberately allows successful writes when Logs is unavailable; there is no retry
queue. Keep Logs running when gathering audit evidence.

## Run the automated tests

```powershell
.\.venv\Scripts\python.exe -m unittest services.assets.test_schema services.assets.test_integration services.assets.test_postman -v
.\.venv\Scripts\python.exe -m pip check
```

Run tests in a fresh Python process. They create separate temporary SQLite files
under locally excluded `.local`, start real Users/Logs/Assets HTTP servers on free
loopback ports, create test-only users, log in through HTTP, and check actual stored
assets and logs. They do not modify the development database. Tables/rows for
future services in these tests are explicitly database fixtures, not implemented
services or submission evidence. Test databases are removed after a successful run.

## Postman and screenshots

The Assets collection now contains **55 requests** and has been executed successfully
through Newman (Postman Runtime). All folders run in order. Folder 4 automatically
creates and cleans up a linked-vulnerability fixture through the implemented API;
no manual SQL setup is required. Never export private passwords, service keys or
populated tokens into Git.

Actual execution records, genuine browser screenshots of the Newman reports,
architecture/ER diagrams, the Word report draft and the detailed screenshot
checklist are under `report/`. These captures are labelled execution reports and
are not represented as Postman desktop screenshots. See `report/TOOLS.md` and
`report/SCREENSHOT_CHECKLIST.md` for the complete workflow and evidence requirements.
