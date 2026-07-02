from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dist = root / "dist"
    work = root / "build" / "pyinstaller-work"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "SSHMountMate",
        "--windowed",
        "--onefile",
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "--specpath",
        str(root / "build"),
        str(root / "src" / "ssh_mountmate" / "__main__.py"),
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
