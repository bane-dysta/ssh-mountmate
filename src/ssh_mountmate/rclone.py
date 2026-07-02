from __future__ import annotations

import shutil
import subprocess
import platform
import os
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


def common_rclone_paths(system: str | None = None) -> list[Path]:
    platform_name = system or platform.system()
    if platform_name == "Windows":
        return []
    home = Path.home()
    return [
        home / ".local" / "bin" / "rclone",
        Path("/opt/homebrew/bin/rclone"),
        Path("/usr/local/bin/rclone"),
        Path("/opt/local/bin/rclone"),
        Path("/usr/bin/rclone"),
        Path("/snap/bin/rclone"),
    ]


def _split_path(value: str) -> list[str]:
    return [part for part in value.split(os.pathsep) if part]


def _read_path_file(path: Path) -> list[str]:
    try:
        return [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip() and not line.strip().startswith("#")]
    except OSError:
        return []


def system_path_entries(system: str | None = None) -> list[str]:
    platform_name = system or platform.system()
    entries: list[str] = []

    if platform_name in {"Darwin", "Linux"}:
        entries.extend(_read_path_file(Path("/etc/paths")))
        paths_dir = Path("/etc/paths.d")
        if paths_dir.exists():
            for path_file in sorted(paths_dir.iterdir()):
                if path_file.is_file():
                    entries.extend(_read_path_file(path_file))

    if platform_name == "Darwin" and Path("/usr/libexec/path_helper").exists():
        try:
            result = subprocess.run(
                ["/usr/libexec/path_helper", "-s"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=3,
            )
            for chunk in result.stdout.replace(";", "\n").splitlines():
                chunk = chunk.strip()
                if chunk.startswith("PATH="):
                    entries.extend(_split_path(chunk.removeprefix("PATH=").strip('"')))
        except Exception:
            pass

    shell = os.environ.get("SHELL")
    if platform_name in {"Darwin", "Linux"} and shell and Path(shell).exists():
        try:
            result = subprocess.run(
                [shell, "-lc", 'printf "%s" "$PATH"'],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=3,
            )
            entries.extend(_split_path(result.stdout))
        except Exception:
            pass

    unique: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if entry not in seen:
            seen.add(entry)
            unique.append(entry)
    return unique


def augment_process_path() -> None:
    current = _split_path(os.environ.get("PATH", ""))
    merged: list[str] = []
    seen: set[str] = set()
    for entry in current + system_path_entries():
        if entry not in seen:
            seen.add(entry)
            merged.append(entry)
    if merged:
        os.environ["PATH"] = os.pathsep.join(merged)


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
    augment_process_path()
    found = shutil.which(current_platform().rclone_binary) or shutil.which("rclone")
    if found:
        return found
    for candidate in common_rclone_paths():
        if candidate.exists():
            return str(candidate)
    return ""


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
