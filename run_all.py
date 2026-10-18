"""Start every implemented service, each in its own process on its own port.

    python run_all.py            # all services that exist
    python run_all.py users logs # only these

Press Ctrl+C to stop them all.
"""
import subprocess
import sys
import time
from pathlib import Path

from common.config import SERVICE_PORTS

ROOT = Path(__file__).resolve().parent


def main():
    wanted = sys.argv[1:] or list(SERVICE_PORTS)
    processes = []
    for name in wanted:
        if name not in SERVICE_PORTS:
            print(f"Unknown service '{name}'. Choose from: {', '.join(SERVICE_PORTS)}")
            continue
        if not (ROOT / "services" / name / "app.py").exists():
            print(f"[skip] {name:16} not implemented yet")
            continue
        process = subprocess.Popen([sys.executable, "-m", f"services.{name}.app"], cwd=ROOT)
        processes.append((name, process))
        print(f"[start] {name:15} http://127.0.0.1:{SERVICE_PORTS[name]}")

    if not processes:
        return
    try:
        while all(p.poll() is None for _, p in processes):
            time.sleep(1)
        for name, process in processes:
            if process.poll() is not None:
                print(f"[stopped] {name} exited with code {process.returncode}")
    except KeyboardInterrupt:
        print("\nStopping all services...")
    finally:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()


if __name__ == "__main__":
    main()
