# Phase 1 Assets verification — historical record (Marc Bteich)

This records the original Assets-only phase. The completed project now has later
services, an automated 55-request Assets collection fixture and actual Newman
execution evidence. See `report/TEST_RESULTS.md` for final integrated results.

Executed locally on **20 October 2026**, using Python 3.13.3 on Windows and the
repository's unchanged pinned requirements in `.venv`.

Final command:

```powershell
.\.venv\Scripts\python.exe -m unittest services.assets.test_schema services.assets.test_integration services.assets.test_postman -v
```

Observed result: **19 tests passed**, `Ran 19 tests in 11.024s`, `OK`.
Subtests exercise many requests and constraint violations within these 19 tests.

| Test group | Tests | Actual coverage and outcome |
|---|---:|---|
| Schema | 7 | Ten tables, integrity and FK checks; owner references; user/asset/incident enums; incident asset SET NULL; note cascade; duplicate threats; CVSS bounds; vulnerability deletion restriction; action step uniqueness and cascade; retained audit username; notification cascade. Passed. |
| HTTP integration | 11 | Real Users/Logs/Assets HTTP servers, real login for all four roles; create/update/delete plus database rows and stored audit events; complete public role matrix; missing/invalid/expired JWTs; service-key isolation; input errors; five search filters and combined/no-match cases; literal SQL injection/wildcard text; missing IDs including oversized IDs; internal lookup/stats; exact counts against SQL; linked-record 409 and rollback; incident preservation; Users/Logs outages; schema compatibility with six existing ORM tables. Passed. |
| Postman packaging | 1 | Parsed 50-request collection; attribution, route coverage, status assertions and blank secrets/tokens. Passed. Does not execute Postman JavaScript. |

The deliberate FK-conflict HTTP test produced the shared error handler's warning
`Integrity error: FOREIGN KEY constraint failed`, returned **409**, preserved the
asset, and generated no successful-deletion audit event. This warning is expected.

Additional executed checks:

- `python -m pip check`: **No broken requirements found**.
- Dependencies installed successfully from the existing `requirements.txt`.
- Real module entrypoints started on **5001 (Users), 5005 (Logs), 5002 (Assets)**;
  each returned **401** with the shared error JSON for an unauthenticated GET.
  Processes were stopped afterward. The normal development SQLite database has
  ten tables, passes integrity checking, and contains zero users and zero assets.
- Existing Users/Incidents/Investigation Notes/Logs/Notifications and new Assets
  ORM column names, types, nullability and FK deletion rules matched `schema.sql`.
- Git inspection confirmed all project changes are additions in Marc's scope;
  no pre-existing tracked files belonging to Elie were modified.
- Local secrets, virtual environment, database, scratch files and instruction
  document patterns were verified as ignored.

Earlier runs and corrections:

- Initial schema-only run: **7 passed**.
- Initial HTTP run: **9 tests passed**, with one schema-comparison failure and a
  teardown error. The test harness used SQLAlchemy reflection that missed inline
  SQLite deletion actions and left SQLite connections open on Windows. The tests
  now inspect actual SQLite FK actions and explicitly close connections.
- Corrected combined run: **17 passed**. Added expired-token/audit-outage coverage:
  **18 passed**. Added oversized-ID coverage and Postman packaging checks: final
  **19 passed** as reported above.

Limits and remaining manual work:

- Tests use isolated temporary databases and explicit test fixtures. They are
  actual executions, but are not screenshots of Marc's Postman session.
- No Postman GUI run, screenshot or submission evidence was generated. Marc must
  run the collection and capture his own request/response and database evidence.
- The Postman conflict folder requires the documented linked-vulnerability fixture
  and must be run separately after setting `linked_asset_id`.
- Schema verification covers SQLite. MySQL execution was not tested.
- Logs-down behavior follows the shared best-effort helper: asset writes succeed
  without an audit row. Users-down behavior rejects owner-dependent writes with
  503. No queues or retry mechanism were added.
- No later service, report endpoint or seed script was implemented in this step.
- Instructor acceptance of a two-person team remains an organizational dependency.
