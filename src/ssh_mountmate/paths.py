from __future__ import annotations

import os
import platform
from pathlib import Path

from . import APP_ID


def user_config_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_ID
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_ID


def user_data_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_ID
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_ID


def servers_file() -> Path:
    return user_config_dir() / "servers.json"


def settings_file() -> Path:
    return user_config_dir() / "settings.json"


def managed_bin_dir() -> Path:
    return user_data_dir() / "bin"
