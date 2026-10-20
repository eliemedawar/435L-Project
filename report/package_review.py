"""Create a source/report review archive from tracked files only.
Developed by: Marc Bteich. Excludes instructions, secrets, databases and tools.
"""
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    folder=ROOT/'.local/submission'
    folder.mkdir(exist_ok=True)
    name='Elie Medawar-Marc Bteich-430L'
    target=folder/(name+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for relative in filter(None,files):
            path=Path(relative)
            if path.name in ('PLAN.md','Sprint1-Brief.docx','.env') or path.name.startswith('PROMPT_'):
                raise RuntimeError('Instruction or secret file unexpectedly tracked')
            if any(part in ('.git','.venv','.local','__pycache__','node_modules') for part in path.parts):
                raise RuntimeError('Local tooling unexpectedly tracked')
            if path.suffix in ('.db','.sqlite3','.pyc'):
                raise RuntimeError('Private database/cache unexpectedly tracked')
            archive.write(ROOT/path,name+'/'+relative)
    print('Created review archive:',target.relative_to(ROOT))
    print('This contains Marc’s draft; combine/review the common report before final Moodle submission.')


if __name__=='__main__':
    main()
