# Local verification and report tools (Marc Bteich)

Runtime requirements remain in Elie's unchanged `requirements.txt`. Additional
tools installed for testing/documentation are separate from the backend:

- Python `python-docx`, `Pillow`, `playwright`; Chromium installed by Playwright.
- Portable Node 22 in locally excluded `.local/node-*-win-x64`, downloaded from
  nodejs.org and checked against its SHA-256 manifest.
- `newman` and `@viz-js/viz` installed only under `.local/tooling`.

These tools and private data are not committed. Tool versions are recorded in
`tool-versions.json`. The report renderer uses local Graphviz WASM to render DOT
to SVG, Playwright to capture actual execution reports and diagrams, and python-docx
to produce the Word draft. It does not simulate the Postman application.

Reproduction (already executed on this machine):

```powershell
.\.venv\Scripts\python.exe -m unittest services.assets.test_schema services.assets.test_integration services.assets.test_postman services.threats.test_integration services.vulnerabilities.test_integration services.playbooks.test_integration services.reports.test_integration_b database.test_seed postman.test_collections -v
.\.venv\Scripts\python.exe postman/build_collections.py
.\.venv\Scripts\python.exe postman/execute.py standalone
.\.venv\Scripts\python.exe postman/execute.py combined
.\.venv\Scripts\python.exe report/generate.py
```

The Postman execution utility starts/stops nine services itself on standard ports,
uses a separate temporary SQLite database and private environment, and saves only
redacted evidence. Stop an already running local backend before rerunning it.
The combined run provisions only admin initially: Elie's original Users tests
create the other accounts. Standalone Person B runs use the seed script.

The normal populated development database is `database/sidrms.db`. Generated
credentials are private in `.local/seed-credentials.json`. They are not submission
files. All generated values and sample rows are development/test data. Do not
export a populated Postman environment into Git.
