from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .paths import managed_bin_dir
from .platforms import current_platform


def bundled_rclone_candidates(app_root: Path) -> list[Path]:
    platform_info = current_platform()
    binary = platform_info.rclone_binary
    return [
        app_root / "bin" / binary,
        app_root / "resources" / "bin" / binary,
    ]


def managed_rclone_path() -> Path:
    return managed_bin_dir() / current_platform().rclone_binary


def resolve_rclone(app_root: Path, configured_path: str = "") -> str:
    if configured_path:
        path = Path(configured_path).expanduser()
        if path.exists():
            return str(path)
    for candidate in bundled_rclone_candidates(app_root):
        if candidate.exists():
            return str(candidate)
    managed = managed_rclone_path()
    if managed.exists():
        return str(managed)
    found = shutil.which(current_platform().rclone_binary) or shutil.which("rclone")
    return found or ""


def rclone_version(rclone_path: str) -> str:
    if not rclone_path:
        return "missing"
    try:
        result = subprocess.run(
            [rclone_path, "version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return "missing"
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    return first_line or "unknown"


def rclone_download_url(version: str = "current", system: str | None = None, arch: str = "amd64") -> str:
    platform_name = system or current_platform().system
    if platform_name == "Windows":
        target = f"rclone-{version}-windows-{arch}.zip"
    elif platform_name == "Darwin":
        target = f"rclone-{version}-osx-{arch}.zip"
    else:
        target = f"rclone-{version}-linux-{arch}.zip"
    return f"https://downloads.rclone.org/{target}"


def manual_install_commands() -> dict[str, list[str]]:
    return {
        "Windows": [
            "winget install --id Rclone.Rclone -e",
            f"Download and unzip: {rclone_download_url(system='Windows')}",
            "Place rclone.exe on PATH or next to SSHMountMate.exe.",
        ],
        "macOS": [
            "brew install rclone",
            "or: curl https://rclone.org/install.sh | sudo bash",
            f"Manual zip: {rclone_download_url(system='Darwin')}",
        ],
        "Linux": [
            "curl https://rclone.org/install.sh | sudo bash",
            "or use your distro package manager, for example: sudo apt install rclone",
            f"Manual zip: {rclone_download_url(system='Linux')}",
        ],
    }


def manual_install_text() -> str:
    lines = ["rclone manual install options", ""]
    for system, commands in manual_install_commands().items():
        lines.append(f"{system}:")
        for command in commands:
            lines.append(f"  {command}")
        lines.append("")
    return "\n".join(lines).rstrip()
