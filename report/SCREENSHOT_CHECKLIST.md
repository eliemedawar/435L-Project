# Evidence checklist (Marc Bteich)

Automated capture is supplied under `screenshots/marc/`. These are genuine browser
screenshots of reports populated from actual Newman/Postman Runtime executions.
They are **not Postman desktop screenshots**. The corresponding complete HTTP
request/response records, timestamps and assertion totals are in `evidence/`.
No API responses or database rows were invented to make a screenshot.

Every caption uses `Marc Bteich – API title – what it does`. Credentials, JWTs and
service keys are redacted. Laboratory indicators/CVEs/scenarios are explicitly
synthetic test data, actually inserted or exercised locally.

## Assets (Marc Bteich)

- [ ] Multiple creations with different types/criticalities/statuses and inserted rows.
- [ ] Update request and record before/after (captured as separate get requests).
- [ ] Admin deletion, analyst denial, and confirmation of deletion.
- [ ] List showing details, criticality and status.
- [ ] Existing asset and nonexistent asset.
- [ ] Name, type, IP, department, criticality, combined and no-match searches.
- [ ] Invalid input; 401/403/404; linked-vulnerability 409 and preserved record.
- [ ] Create/update/delete audit records and permission-denial audit records.

## Threat Intelligence (Marc Bteich)

- [ ] Multiple indicators and actual stored records; explain each type/severity.
- [ ] List, detail and nonexistent threat.
- [ ] Type/value/severity/source and combined searches.
- [ ] Update before/after; admin deletion and denied deletion.
- [ ] Invalid IP/domain/hash/severity; duplicate normalized type/value 409.
- [ ] Critical threat notifications for every admin and mutation audit events.

## Vulnerabilities (Marc Bteich)

- [ ] Multiple severities/statuses in stored records (seed samples are labelled snapshots).
- [ ] Create, list, detail and nonexistent ID.
- [ ] CVE/severity/asset/status searches.
- [ ] Actual Open → Under Investigation → In Progress → Resolved → Closed requests.
- [ ] Invalid skipped/backward statuses and automatic resolution_date.
- [ ] Invalid CVE/CVSS, nonexistent asset, prohibited create/delete/update roles.
- [ ] Critical notifications, audit rows, admin delete and resulting stored records.

## Playbooks and Response Actions (Marc Bteich)

- [ ] Multiple playbooks with category/severity and actual stored rows.
- [ ] List, detail and nonexistent ID.
- [ ] Actions inserted out of order and returned sorted by step_number.
- [ ] Duplicate step 409; same step allowed in a different playbook (HTTP tests).
- [ ] Assignment and Pending → In Progress → Completed with completion_date.
- [ ] Execution history with actor/timestamp/assignment/status snapshots.
- [ ] Invalid transitions, invalid assignee and unauthorized operations.
- [ ] Cascade deletion; surviving archived history in Logs. Logs outage must preserve playbook.

## Reports and database (Marc Bteich)

- [ ] Assets report: total, critical count, by type; compare to SQL counts.
- [ ] Threat report: total, severity/type grouping, latest five; compare to SQL.
- [ ] Vulnerability report: total, critical count, severity/status grouping; compare to SQL.
- [ ] Admin/auditor success, analyst/user denial and unauthenticated denial.
- [ ] Ten tables, columns, primary/foreign keys, relationships and stored records.
- [ ] Architecture and ER diagrams, with design/deletion/history explanations.

## Personal acceptance review (Marc Bteich)

- [ ] Review images at readable scale and choose evidence matching each claim.
- [ ] If the professor insists on Postman desktop UI specifically, repeat the
  demonstrated cases in Postman and add authentic GUI captures. Do not relabel
  Newman-report captures as GUI screenshots.
- [ ] Incorporate Elie's report sections and his own evidence, update page numbers
  and contents, review AI-use disclosure, and ensure every title has its owner's name.
