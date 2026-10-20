# Security Incident Detection and Response Backend

EECE/Software Tools Lab Sprint 1. **Elie Medawar (Person A)** and **Marc Bteich (Person B)**.

Nine independent Flask apps share a database and `common/` infrastructure. Public
protected endpoints use Bearer JWTs; internal HTTP calls use `X-Service-Key`.
SQLite development is implemented and tested. No frontend or deployment is required.

| Port | Service | Owner |
|---|---|---|
| 5001 | Users / Identity | Elie |
| 5002 | Assets | Marc |
| 5003 | Incidents | Elie |
| 5004 | Threat Intelligence | Marc |
| 5005 | Audit Logs | Elie |
| 5006 | Reports | Both |
| 5007 | Vulnerabilities | Marc |
| 5008 | Notifications | Elie |
| 5009 | Playbooks / Response Actions | Marc |

## Local setup

On Marc's current machine setup, seeding, tests and startup have already been
performed. On a new installation, create a virtual environment, install
`requirements.txt`, copy `.env.example` to `.env`, replace both placeholder secrets
with distinct random values, and run:

```powershell
.\.venv\Scripts\python.exe -m database.seed
.\.venv\Scripts\python.exe run_all.py
```

`database/schema.sql` is the complete SQLite DDL for creating a fresh database;
the ORM also creates missing tables on startup. The seed upgrades the action-history
column when using a database from Phase 1. It is additive/idempotent and never
resets existing passwords. Sample accounts: admin/admin2, lara (analyst), nadia
(auditor), rami (user), plus inactive/suspended lab users. Generated passwords are
private in `.local/seed-credentials.json`; inspect locally, never commit/export them.

Seeding creates labelled synthetic lab indicators, CVE-format examples and lifecycle
snapshots. They are sample data, not claims about real threats or genuine CVEs.
JWTs, service keys, `.env`, local databases, virtual environments and instruction
documents must stay out of Git and submission archives.

## Implementation and verification

Each service has routes and a service/validator class; models are registered
automatically. Elie's shared code and original collections are preserved.
Reports collect data over HTTP. Critical threat/vulnerability creates notify all
admins. Vulnerability/action transitions must advance exactly one step. Actions
store transactional execution history and archive it through Logs before deletion.
Consequently a Logs outage blocks playbook deletion to preserve execution history;
ordinary audit/notification calls retain the shared best-effort behavior.

See [test results](report/TEST_RESULTS.md), [tooling/reproduction](report/TOOLS.md),
[API documentation](report/API_DOCUMENTATION.md), [Person B report](report/PERSON_B_REPORT.md),
and [evidence checklist](report/SCREENSHOT_CHECKLIST.md). The Word draft is
`report/Person_B_Report.docx`. Actual redacted Newman records and genuine browser
captures of execution reports are included; they do not claim to be Postman GUI screenshots.

The individual collections and merged `postman/SIDRMS.postman_collection.json`
are executable. The combined collection requires a **fresh isolated database with
only admin provisioned**, since the Users folder intentionally registers accounts.
`postman/execute.py` provisions that environment automatically. Do not run destructive
integration scenarios against an important database. Standalone B collections use
the seeded accounts and automatically provision/clean their relationship fixtures.

## Submission review

Marc must review/adapt and be able to explain all assisted code and prose, then
combine his draft with Elie's report/evidence and confirm the instructor accepts
the two-person arrangement and supplied evidence format. Both students attend
CREATES at least three days before the deadline, disclose AI assistance, and upload
the same reviewed package. Remote pushes, PRs and merges require Marc's approval.
