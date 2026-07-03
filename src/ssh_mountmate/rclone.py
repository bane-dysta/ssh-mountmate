from __future__ import annotations

import shutil
import subprocess
import platform
import os
import stat
import tempfile
import urllib.request
import zipfile
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


def rclone_download_arch(machine: str | None = None) -> str:
    value = (machine or platform.machine()).lower()
    if value in {"x86_64", "amd64"}:
        return "amd64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    if value in {"i386", "i686", "x86"}:
        return "386"
    return "amd64"


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


def install_rclone_to(target_dir: Path) -> Path:
    platform_info = current_platform()
    binary = platform_info.rclone_binary
    arch = rclone_download_arch()
    url = rclone_download_url(system=platform_info.system, arch=arch)
    target = target_dir / binary
    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ssh-mountmate-rclone-") as temp_name:
        temp = Path(temp_name)
        archive = temp / "rclone.zip"
        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as zf:
            members = [member for member in zf.namelist() if Path(member).name == binary and not member.endswith("/")]
            if not members:
                raise RuntimeError(f"Downloaded rclone archive did not contain {binary}: {url}")
            extracted = Path(zf.extract(members[0], temp))
            shutil.copy2(extracted, target)

    if platform_info.system != "Windows":
        mode = target.stat().st_mode
        target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def install_managed_rclone() -> Path:
    return install_rclone_to(managed_bin_dir())


LINUX_DEPENDENCY_COMMANDS = [
    {
        "label": "Debian family (Debian, Ubuntu, Linux Mint, Pop!_OS)",
        "ids": {"debian", "ubuntu", "linuxmint", "pop"},
        "likes": {"debian", "ubuntu"},
        "command": "sudo apt update && sudo apt install -y fuse3 openssh-client",
    },
    {
        "label": "Fedora/RHEL family (Fedora, RHEL, CentOS Stream, Rocky Linux, AlmaLinux)",
        "ids": {"fedora", "rhel", "centos", "rocky", "almalinux"},
        "likes": {"fedora", "rhel", "centos"},
        "command": "sudo dnf install -y fuse3 openssh-clients",
    },
    {
        "label": "Arch family (Arch Linux, Manjaro, EndeavourOS)",
        "ids": {"arch", "manjaro", "endeavouros"},
        "likes": {"arch"},
        "command": "sudo pacman -S --needed fuse3 openssh",
    },
    {
        "label": "openSUSE/SUSE family (openSUSE Leap, Tumbleweed, SLES)",
        "ids": {"opensuse", "opensuse-leap", "opensuse-tumbleweed", "sles"},
        "likes": {"suse", "opensuse"},
        "command": "sudo zypper install -y fuse3 openssh",
    },
]


def linux_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return {}
    data: dict[str, str] = {}
    for line in lines:
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"').strip("'")
    return data


def preferred_linux_dependency_command() -> tuple[str, str] | None:
    release = linux_os_release()
    distro_id = release.get("ID", "").lower()
    id_like = set(release.get("ID_LIKE", "").lower().split())
    for item in LINUX_DEPENDENCY_COMMANDS:
        if distro_id in item["ids"] or id_like.intersection(item["likes"]):
            return str(item["label"]), str(item["command"])
    return None


def manual_install_commands() -> dict[str, list[str]]:
    linux_commands = [
        "rclone:",
        "curl https://rclone.org/install.sh | sudo bash",
        "or use your distro package manager, for example: sudo apt install rclone",
        f"Manual zip: {rclone_download_url(system='Linux')}",
        "",
        "FUSE and OpenSSH:",
    ]
    preferred = preferred_linux_dependency_command() if platform.system() == "Linux" else None
    if preferred:
        label, command = preferred
        linux_commands.extend(["Recommended for this system:", label, command, ""])
    linux_commands.append("All common distro commands:")
    for item in LINUX_DEPENDENCY_COMMANDS:
        linux_commands.extend([str(item["label"]) + ":", str(item["command"])])

    return {
        "Windows": [
            "rclone:",
            "winget install --id Rclone.Rclone -e",
            f"Download and unzip: {rclone_download_url(system='Windows')}",
            "Place rclone.exe on PATH or next to SSHMountMate.exe.",
            "",
            "WinFsp:",
            "winget install --id WinFsp.WinFsp -e",
            "or download the installer from: https://winfsp.dev/rel/",
            "",
            "OpenSSH Client:",
            'powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"',
        ],
        "macOS": [
            "rclone:",
            "Do not use the Homebrew rclone package for mounts; Homebrew rclone cannot run rclone mount on macOS.",
            "curl https://rclone.org/install.sh | sudo bash",
            f"Manual zip: {rclone_download_url(system='Darwin')}",
            "",
            "macFUSE:",
            "Install macFUSE with Homebrew Cask: brew install --cask macfuse",
            "If macFUSE asks for approval, enable it in System Settings -> Privacy & Security, then retry.",
            "",
            "OpenSSH Client:",
            "OpenSSH is normally included with macOS. If ssh is missing, run: xcode-select --install",
        ],
        "Linux": linux_commands,
    }


def manual_install_text() -> str:
    lines = ["manual dependency install options", ""]
    for system, commands in manual_install_commands().items():
        lines.append(f"{system}:")
        for command in commands:
            lines.append(f"  {command}" if command else "")
        lines.append("")
    return "\n".join(lines).rstrip()
