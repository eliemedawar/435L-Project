# Final verification (Marc Bteich)

Executed on 20 October 2026, on Marc's local Windows environment, Python 3.13.3.

| Verification | Executed result |
|---|---|
| Automated Python suite | **34 tests passed**, 50.450 seconds |
| Assets Newman | 55 requests, 112 assertions, zero failures |
| Threats Newman | 31 requests, 62 assertions, zero failures |
| Vulnerabilities Newman | 34 requests, 70 assertions, zero failures |
| Playbooks Newman | 27 requests, 57 assertions, zero failures |
| Person B reports Newman | 19 requests, 38 assertions, zero failures |
| Full merged Newman, including unchanged A requests | **336 requests, 679 assertions, zero failures** |
| Total final Newman runs | **502 requests, 1,018 assertions, zero failures** |
| Live populated backend | All nine services authenticated successfully; all six reports returned 200; source totals matched SQL |
| Database | Integrity OK, no foreign-key violations, all ten ORM column definitions matched schema.sql |
| Dependency consistency | pip check: no broken requirements |

Python suite: Assets/schema/packaging 19 tests; Threats 4; Vulnerabilities 3;
Playbooks 4; Reports/integration 2; seed/schema alignment 1; merge preservation 1.
Tests include multiple HTTP requests and subcases, not one request per test.

The live backend is launched with the existing `run_all.py`, bound to loopback
ports 5001–5009. Process details and runtime logs remain in excluded `.local`.
`evidence/live-backend.json` records the actual check and database/report totals.

Scope of actual verification: all Person B public routes and internal stats;
complete role matrices; required fields and wrong types; IPv4/IPv6, domain and
MD5/SHA1/SHA256 formats; normalized duplicates; CVE/CVSS bounds; asset/user FKs;
valid/invalid remediation and action lifecycles; automatic timestamps; ordering;
durable action history and archive-before-cascade; notifications to all admins;
real audit records; source statistics; source unavailability; original incident
assignment/status/notification workflow; original A requests/scripts in Newman.

Corrections during this session:

- The first standalone Newman run passed every assertion but hit a Windows
  temporary-file cleanup race. The runner now retries bounded cleanup; final
  standalone and merged runs exited successfully.
- The first merged run had one failed assertion because the merge omitted Elie's
  collection-level `today` pre-request hook. The merge now preserves collection
  hooks as folder hooks. Elie's original file was never changed. The final merged
  run passed all 679 assertions, including that date search.
- Action history is now archived via acknowledged audit HTTP calls before a
  playbook is deleted, preventing loss when Logs is unavailable. The test suite
  and final Newman runs include the final implementation.

Evidence boundaries: screenshots are genuine browser captures of redacted actual
Newman execution reports and actual SQLite inspection, not Postman desktop UI.
Lab records/CVEs/indicators are synthetic samples, explicitly labelled. Seeded
status/history snapshots are distinct from actual lifecycle API executions.
MySQL, external deployment and instructor acceptance were not tested or claimed.
