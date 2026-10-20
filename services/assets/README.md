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
ten tables and no user accounts. On a fresh clone, before starting any services,
initialize the full schema once with the following command. It refuses to overwrite
an existing database:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; import sqlite3; p=Path('database/sidrms.db'); assert not p.exists(), 'Database already exists: do not overwrite it'; c=sqlite3.connect(p); c.executescript(Path('database/schema.sql').read_text()); c.close(); print('Created all ten tables')"
```

`schema.sql` targets **SQLite development**, as permitted by the plan. It is not a
MySQL import script. The five tables owned by future B services are present in the
schema, but their services and ORM models have not been implemented in this step.
The existing six ORM tables (including Assets) match the script's columns, types,
nullability and foreign-key deletion rules. Status transitions, IP/CVE formats,
and audit immutability also need application validation; SQL enum checks alone
do not enforce these rules. Existing Logs code prevents ORM updates to audit logs.

Create your first administrator using Elie's existing command. It asks for the
password privately; the password must satisfy his password rules:

```powershell
.\.venv\Scripts\python.exe -m services.users.create_admin --username admin --email marc@example.test --full-name "Marc Bteich" --department Security
.\.venv\Scripts\python.exe run_all.py users logs assets
```

Stop with Ctrl+C. To run only Assets when Users and Logs are already running:

```powershell
.\.venv\Scripts\python.exe -m services.assets.app
```

Use the Users service to log in and create an analyst, auditor and regular user
as admin. Elie's Users Postman collection provides those requests. The Assets
collection defaults to account names `admin`, `lara`, `nadia`, and `rami`; adjust
them to match your actual accounts. No demo passwords or accounts are preloaded.

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

Import `postman/assets.postman_collection.json` (50 requests). Set the four account
names/passwords and `service_key` in a private local Postman environment. Do not
export secrets or populated tokens into Git. Folders 0–3 can be run in order;
folder 4 is a separate manual conflict test. Login saves tokens and owner_id;
asset creation saves asset_id. Sample requests intentionally insert multiple assets;
repeated runs add more samples. Each request has Marc's full name, expected status
and response assertions. Automated HTTP tests have run; the Postman GUI collection
has not been executed or photographed by Codex.

For folder 4, create an asset through Postman, set `linked_asset_id` to its ID, then
insert a clearly identified test vulnerability using a database tool connected to
your development database. Bind `:asset_id` to that actual ID:

```sql
PRAGMA foreign_keys = ON;
INSERT INTO vulnerabilities
 (title, description, cve_id, cvss_score, severity, asset_id, discovery_source, status, created_at)
VALUES
 ('Assets FK test', 'Temporary test fixture', 'CVE-2026-1234', 9.8, 'Critical',
  :asset_id, 'Local test fixture', 'Open', CURRENT_TIMESTAMP);
```

Commit the database transaction, run folder 4 and expect 409. Confirm that the
asset still exists. Remove only your temporary vulnerability row afterward. This
is test data for verifying FK protection; it is not a claim about a real CVE or
evidence that Service 7 exists.

Capture screenshots yourself from your running system:

1. Multiple successful creates, with request/response and actual inserted rows.
2. Update request/response and before/after database rows.
3. Successful delete, unauthorized delete, and rows confirming the outcome.
4. List response showing details, criticality and status.
5. Existing ID and missing-ID responses.
6. Each of the five search criteria, combined filters and a no-match case.
7. 400, 401, 403, 404 and the linked-record 409, showing actual input/output.
8. Audit rows for create/update/delete and permission denial.
9. All ten tables, PKs/FKs, relationships and real stored records. An ER diagram
   and design explanation are still required for the later report work.

Every caption must read `Marc Bteich – API title – what it does`. Hide passwords,
tokens and service keys. Code screenshots do not count as operation evidence.
Explain at least three APIs in the report and disclose where and why AI helped;
review and adapt the implementation so you can defend it yourself.
