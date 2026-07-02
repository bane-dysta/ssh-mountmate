from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PlatformCapabilities:
    system: str
    rclone_binary: str
    mount_dependency_name: str
    supports_drive_letters: bool

    def default_mountpoint(self, name: str) -> str:
        safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name) or "remote"
        if self.system == "Windows":
            return "Auto"
        if self.system == "Darwin":
            return str(Path.home() / "Volumes" / safe_name)
        return str(Path.home() / "mnt" / safe_name)

    def mount_dependency_installed(self) -> bool:
        if self.system == "Windows":
            # Real implementation should check WinFsp registry/install paths.
            return False
        if self.system == "Darwin":
            # Real implementation should check macFUSE.
            return False
        return shutil.which("fusermount3") is not None or shutil.which("fusermount") is not None


def current_platform() -> PlatformCapabilities:
    system = platform.system()
    if system == "Windows":
        return PlatformCapabilities(system, "rclone.exe", "WinFsp", True)
    if system == "Darwin":
        return PlatformCapabilities(system, "rclone", "macFUSE", False)
    return PlatformCapabilities(system, "rclone", "FUSE", False)
