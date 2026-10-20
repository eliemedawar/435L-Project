"""Build the one common final report (Word) from both members' sections and genuine evidence.
Developed by: Elie Medawar.

    python report/build_final_report.py

Inputs: report/PERSON_A_REPORT.md (Elie), report/PERSON_B_REPORT.md and report/API_DOCUMENTATION.md (Marc),
the evidence screenshots in report/screenshots/{elie,marc}, and the SVG diagrams. Output:
report/Final_Report.docx. Microsoft Edge (headless) renders the diagrams and the GitHub history pages.
"""
import json
from pathlib import Path
import re
import subprocess
import time

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
SHOTS_A = REPORT / "screenshots/elie"
SHOTS_B = REPORT / "screenshots/marc"
GITHUB = REPORT / "screenshots/github"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
REPO = "https://github.com/eliemedawar/435L-Project"
TEAM = ("Elie Medawar", "Marc Bteich", "Zoulfikar Shokor")
TODAY = time.strftime("%d %B %Y").lstrip("0")


# ---------------------------------------------------------------- rendering helpers
def edge_capture(url, png, width=1400, height=2400, wait_ms=0):
    png.unlink(missing_ok=True)
    args = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            f"--user-data-dir={ROOT / '.local/edge-profiles' / png.stem}", "--force-device-scale-factor=1",
            f"--window-size={width},{height}", f"--screenshot={png}"]
    if wait_ms:
        args.append(f"--virtual-time-budget={wait_ms}")
    for attempt in range(8):
        subprocess.run(args + [url], capture_output=True, timeout=120)
        if png.exists():
            return trim(png)
        time.sleep(1 + attempt)
    raise RuntimeError(f"Edge did not produce {png.name}")


def trim(png, margin=16):
    with Image.open(png) as image:
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, rgb.getpixel((rgb.width - 2, rgb.height - 2)))
        box = ImageChops.difference(rgb, background).getbbox()
        if box:
            left, top, right, bottom = box
            rgb = rgb.crop((max(0, left - margin), max(0, top - margin),
                            min(rgb.width, right + margin), min(rgb.height, bottom + margin)))
        rgb.save(png)
    return png


def render_assets():
    diagrams = REPORT / "diagrams"
    for name in ("architecture", "database"):
        if not (diagrams / f"{name}.png").exists():
            edge_capture((diagrams / f"{name}.svg").as_uri(), diagrams / f"{name}.png", 2000, 2000)
    GITHUB.mkdir(parents=True, exist_ok=True)
    if not any(GITHUB.glob("github-*.png")):
        github_history_page()


def github_history_page():
    """Fallback when github.com pages cannot be captured: the same history from GitHub's public API."""
    import html
    import requests
    api = "https://api.github.com/repos/eliemedawar/435L-Project"
    commits = requests.get(f"{api}/commits", params={"sha": "main", "per_page": 100}, timeout=90).json()
    contributors = requests.get(f"{api}/contributors", timeout=90).json()
    branches = requests.get(f"{api}/branches", timeout=90).json()
    rows = "".join(f"<tr><td>{c['sha'][:7]}</td><td>{html.escape(c['commit']['author']['name'])}</td>"
                   f"<td>{c['commit']['author']['date'][:16].replace('T', ' ')}</td>"
                   f"<td>{html.escape(c['commit']['message'].splitlines()[0])}</td></tr>" for c in commits)
    people = "".join(f"<tr><td>{html.escape(c['login'])}</td><td>{c['contributions']}</td></tr>" for c in contributors)
    names = ", ".join(html.escape(b["name"]) for b in branches)
    style = ("<style>body{font:15px Arial;margin:28px;color:#172033;background:#fff}table{border-collapse:collapse;"
             "margin-bottom:22px}td,th{border:1px solid #cbd5e1;padding:6px 9px;text-align:left}th{background:#dbeafe}</style>")
    page = REPORT / "evidence/github-history.html"
    page.write_text(f"<!doctype html><meta charset='utf-8'>{style}<h1>GitHub history – {REPO}</h1>"
                    f"<p>Retrieved live from the GitHub API on {TODAY}.</p><h2>Branches</h2><p>{names}</p>"
                    f"<h2>Contributors (commits on the default branch)</h2><table><tr><th>GitHub account</th><th>Commits</th></tr>{people}</table>"
                    f"<h2>Commit history on main</h2><table><tr><th>Commit</th><th>Author</th><th>Date (UTC)</th><th>Message</th></tr>{rows}</table>",
                    encoding="utf-8")
    edge_capture(page.as_uri(), GITHUB / "github-history.png", 1400, 4000)


# ---------------------------------------------------------------- docx helpers
def set_cell_shading(cell, hex_fill):
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), hex_fill)
    cell._tc.get_or_add_tcPr().append(shading)


def add_runs(paragraph, text):
    """Inline **bold**, `code` and [text](url) (links shown as text + url)."""
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
        else:
            paragraph.add_run(part)


def add_picture(document, png, caption=None, width_in=6.3):
    """Add an image with its caption; very tall images are split into page-sized slices."""
    if caption:
        p = document.add_paragraph()
        run = p.add_run(caption)
        run.bold = True
        run.font.size = Pt(9.5)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(8)
    with Image.open(png) as image:
        width, height = image.size
        max_ratio = 1.25
        if height / width <= max_ratio:
            document.add_picture(str(png), width=Inches(width_in))
            return
        slice_h = int(width * max_ratio)
        for index, top in enumerate(range(0, height, slice_h)):
            part = png.parent / f".{png.stem}-part{index}.png"
            image.crop((0, top, width, min(height, top + slice_h))).save(part)
            document.add_picture(str(part), width=Inches(width_in))
            part.unlink()


def add_table(document, rows):
    if not rows:
        return
    header, body = rows[0], rows[1:]
    table = document.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, header):
        cell.text = ""
        add_runs(cell.paragraphs[0], text)
        for run in cell.paragraphs[0].runs:
            run.bold = True
        set_cell_shading(cell, "DBEAFE")
    for row in body:
        cells = table.add_row().cells
        for cell, text in zip(cells, row + [""] * (len(header) - len(row))):
            cell.text = ""
            add_runs(cell.paragraphs[0], text)
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    document.add_paragraph()


def add_markdown(document, text, base_dir, heading_offset=0, shot_handler=None):
    """Small Markdown renderer: headings, paragraphs, lists, pipe tables, code blocks, images, [[shot]] tags."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            p = document.add_paragraph()
            run = p.add_run("\n".join(block))
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            level = min(max(len(heading.group(1)) - 1 + heading_offset, 1), 4)
            document.add_heading(heading.group(2).strip(), level=level)
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            add_table(document, rows)
            continue
        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if image:
            path = (base_dir / image.group(2)).resolve()
            if path.exists():
                add_picture(document, path, image.group(1))
            i += 1
            continue
        tag = re.match(r"^\[\[(.+?)\]\]$", line.strip())
        if tag and shot_handler:
            shot_handler(document, tag.group(1))
            i += 1
            continue
        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        numbered = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if bullet or numbered:
            p = document.add_paragraph(style="List Bullet" if bullet else "List Number")
            add_runs(p, (bullet or numbered).group(1))
            i += 1
            continue
        paragraph = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|!\[|\[\[|\s*[-*]\s|\s*\d+\.\s)", lines[i]):
            paragraph.append(lines[i].strip())
            i += 1
        add_runs(document.add_paragraph(), " ".join(paragraph))


def sections(markdown_text, level="## "):
    """Split Markdown into {heading: body} at the given heading level (sub-headings stay in the body)."""
    result, current = {}, None
    for line in markdown_text.splitlines():
        if line.startswith(level) and not line.startswith(level + "#"):
            current = line[len(level):].strip()
            result[current] = []
        elif current:
            result[current].append(line)
    return {k: "\n".join(v).strip() for k, v in result.items()}


def add_toc(document):
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Right-click and choose Update Field to refresh page numbers."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, placeholder, end):
        run._r.append(element)
    settings = document.settings.element
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    settings.append(update)


def page_break(document):
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------- evidence selection
def elie_shot_handler():
    manifest = {c["name"]: c for c in json.loads((REPORT / "evidence/screenshot-manifest-elie.json").read_text(encoding="utf-8"))}

    def handler(document, tag):
        if tag == "github":
            for name, caption in (("github-branches", "GitHub – branches of both members"),
                                  ("github-commits", "GitHub – commit history on main"),
                                  ("github-contributors", "GitHub – Insights, contributors"),
                                  ("github-pull-1", "GitHub – pull request #1 (Elie Medawar's services) merged"),
                                  ("github-history", "GitHub – branches, contributors and full commit history of main")):
                if (GITHUB / f"{name}.png").exists():
                    add_picture(document, GITHUB / f"{name}.png", caption)
        elif tag == "db":
            add_picture(document, SHOTS_A / "database-inspection-elie.png",
                        "Elie Medawar – Database records – users, incidents, notes, notifications, logs")
        elif tag.startswith("shot:"):
            name = "newman-" + tag[5:]
            add_picture(document, SHOTS_A / f"{name}.png", manifest[name]["caption"])
    return handler


def marc_cards():
    """Pick representative screenshots of each of Marc's collections: the first of each method/status pair."""
    chosen = {}
    for card in json.loads((REPORT / "evidence/screenshot-manifest.json").read_text(encoding="utf-8")):
        collection = card["name"].split("-")[1]
        picked = chosen.setdefault(collection, [])
        if len(picked) < 9 and all((c["method"], c["status"]) != (card["method"], card["status"]) for c in picked):
            picked.append(card)
    return chosen


# ---------------------------------------------------------------- build
def main():
    render_assets()
    elie = sections((REPORT / "PERSON_A_REPORT.md").read_text(encoding="utf-8"))
    marc_text = (REPORT / "PERSON_B_REPORT.md").read_text(encoding="utf-8")
    marc = sections(marc_text)
    marc5 = sections(marc["5. Implementation Details (Marc Bteich)"], "### ")
    marc_shots = marc_cards()
    shot = elie_shot_handler()

    def marc_evidence(document, collection):
        for card in marc_shots.get(collection, []):
            add_picture(document, SHOTS_B / f"{card['name']}.png", card["caption"])

    def elie_section(document, key, title):
        document.add_heading(title, level=1 if title[0].isdigit() and "." not in title.split()[0][:-1] else 2)
        add_markdown(document, elie[key], REPORT, heading_offset=1, shot_handler=shot)

    document = Document()
    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    # 1. Title page
    for _ in range(5):
        document.add_paragraph()
    for text, size, bold in (("Security Incident Detection and Response Management System", 24, True),
                             ("Backend – Final Project, Sprint I", 16, False),
                             ("Software Tools Lab (430L)", 13, False)):
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.font.size = Pt(size)
        run.bold = bold
    document.add_paragraph()
    for text in ("Students: " + ", ".join(TEAM), f"Date of submission: {TODAY}", f"GitHub repository: {REPO}",
                 "Title page and table of contents: (Elie Medawar)"):
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(text).font.size = Pt(12)
    page_break(document)

    # 2. Table of contents
    document.add_heading("2. Table of Contents (Elie Medawar)", level=1)
    add_toc(document)
    add_table(document, [["Section", "Responsible member"],
        ["1. Title Page", "Elie Medawar"], ["2. Table of Contents", "Elie Medawar"],
        ["3. Introduction", "Marc Bteich"], ["4. System Architecture", "Marc Bteich"],
        ["5.1 Users and Identity Management Service", "Elie Medawar"], ["5.2 Asset Management Service", "Marc Bteich"],
        ["5.3 Incident Management Service", "Elie Medawar"], ["5.4 Threat Intelligence Service", "Marc Bteich"],
        ["5.5 Security Audit Logging Service", "Elie Medawar"],
        ["5.6 Security Reports Service", "Elie Medawar (summary, incidents, activity); Marc Bteich (assets, threats, vulnerabilities)"],
        ["5.7 Vulnerability Management Service", "Marc Bteich"], ["5.8 Notification and Alert Management Service", "Elie Medawar"],
        ["5.9 Security Playbook and Response Automation Service", "Marc Bteich"], ["6. Database Design", "Marc Bteich"],
        ["7. Error Handling and Validation", "Elie Medawar"], ["8. API Documentation", "Marc Bteich"],
        ["9. Authentication and Authorization", "Elie Medawar"], ["10. GitHub and Version Control", "Elie Medawar"],
        ["11. References", "Elie Medawar, Marc Bteich"]])
    p = document.add_paragraph()
    p.add_run("Evidence note: every API screenshot is a browser capture of a genuine Newman (Postman runtime) execution "
              "record from the team's running system, with credentials and tokens redacted. Each caption names the "
              "student who developed the API, the API title and what the request does.").italic = True
    page_break(document)

    # 3, 4 (Marc)
    for key in ("3. Introduction (Marc Bteich)", "4. System Architecture (Marc Bteich)"):
        document.add_heading(key, level=1)
        add_markdown(document, marc[key], REPORT, heading_offset=1)

    # 5. Implementation details, in service order
    document.add_heading("5. Implementation Details (Elie Medawar, Marc Bteich)", level=1)
    plan = [
        ("A", "5.1 Users and Identity Management Service (Elie Medawar)", None),
        ("B", "5.2 Asset Management Service (Marc Bteich)", ("Assets (Marc Bteich)", "assets")),
        ("A", "5.3 Incident Management Service (Elie Medawar)", None),
        ("B", "5.4 Threat Intelligence Service (Marc Bteich)", ("Threat Intelligence (Marc Bteich)", "threats")),
        ("A", "5.5 Security Audit Logging Service (Elie Medawar)", None),
        ("A", "5.6 Security Reports Service – Summary, Incident and Activity Reports (Elie Medawar)", None),
        ("B", "5.6 Security Reports Service – Asset, Threat and Vulnerability Reports (Marc Bteich)",
         ("Reports and service communication (Marc Bteich)", "reports_b")),
        ("B", "5.7 Vulnerability Management Service (Marc Bteich)", ("Vulnerability Management (Marc Bteich)", "vulnerabilities")),
        ("A", "5.8 Notification and Alert Management Service (Elie Medawar)", None),
        ("B", "5.9 Security Playbook and Response Automation Service (Marc Bteich)",
         ("Playbooks and Response Actions (Marc Bteich)", "playbooks")),
    ]
    for owner, title, source in plan:
        document.add_heading(title, level=2)
        if owner == "A":
            add_markdown(document, elie[title], REPORT, heading_offset=2, shot_handler=shot)
        else:
            add_markdown(document, marc5[source[0]], REPORT, heading_offset=2)
            marc_evidence(document, source[1])

    # 6 (Marc) + database screenshots of both members
    key = "6. Database Design (Marc Bteich)"
    document.add_heading(key, level=1)
    add_markdown(document, marc[key], REPORT, heading_offset=1)
    if (SHOTS_B / "database-inspection.png").exists():
        add_picture(document, SHOTS_B / "database-inspection.png",
                    "Marc Bteich – Database structure and stored records – actual local SQLite inspection")
    add_picture(document, SHOTS_A / "database-inspection-elie.png",
                "Elie Medawar – Database records after the Newman run – users, incidents, investigation_notes, notifications, logs")

    # 7 (Elie)
    document.add_heading("7. Error Handling and Validation (Elie Medawar)", level=1)
    add_markdown(document, elie["7. Error Handling and Validation (Elie Medawar)"], REPORT, heading_offset=1, shot_handler=shot)

    # 8 (Marc): summary paragraph + the full merged endpoint reference
    key = "8. API Documentation (Marc Bteich)"
    document.add_heading(key, level=1)
    add_markdown(document, marc[key], REPORT, heading_offset=1)
    api = (REPORT / "API_DOCUMENTATION.md").read_text(encoding="utf-8").split("\n", 1)[1]
    add_markdown(document, api, REPORT, heading_offset=1)

    # 9, 10 (Elie)
    for title in ("9. Authentication and Authorization (Elie Medawar)", "10. GitHub and Version Control (Elie Medawar)"):
        document.add_heading(title, level=1)
        add_markdown(document, elie[title], REPORT, heading_offset=1, shot_handler=shot)

    # 11. References (both)
    document.add_heading("11. References (Elie Medawar, Marc Bteich)", level=1)
    for ref in ("Course brief: Final Project Fall 2026-2027 – Sprint I.",
                "Flask documentation – https://flask.palletsprojects.com/",
                "Flask-SQLAlchemy documentation – https://flask-sqlalchemy.readthedocs.io/",
                "SQLAlchemy 2.0 documentation – https://docs.sqlalchemy.org/en/20/",
                "PyJWT documentation – https://pyjwt.readthedocs.io/",
                "bcrypt for Python – https://pypi.org/project/bcrypt/",
                "SQLite foreign key support – https://www.sqlite.org/foreignkeys.html",
                "Python ipaddress – https://docs.python.org/3/library/ipaddress.html",
                "Postman collection format and Newman – https://learning.postman.com/docs/reference/newman-cli/command-line-integration-with-newman/",
                "OWASP Top 10 (injection, broken access control) – https://owasp.org/Top10/"):
        add_runs(document.add_paragraph(style="List Bullet"), ref)
    document.add_heading("Use of AI tools", level=2)
    add_runs(document.add_paragraph(), "**Elie Medawar:** Claude Code (Anthropic) was used to split the work between "
             "the members; to generate a first version of the shared common/ package, the Users, Incident Management, "
             "Audit Logging and Notification services, the summary/incident/activity reports and their Postman "
             "collections; to write test and evidence scripts; and to draft Elie Medawar's report sections and assemble "
             "this document. Purpose: to speed up repetitive code and documentation. Elie Medawar reviewed, ran and "
             "tested the work and can explain each design decision. All execution evidence comes from the team's own "
             "running system.")
    marc_ai = [line for line in marc["11. References and AI-use Disclosure (Marc Bteich)"].split("\n\n")
               if line.startswith("AI-use disclosure")]
    if marc_ai:
        add_runs(document.add_paragraph(), "**Marc Bteich:** " + marc_ai[0].split(":", 1)[1].strip())

    out = REPORT / "Final_Report.docx"
    document.save(out)
    print(f"Saved {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
