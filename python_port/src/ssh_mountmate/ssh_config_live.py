from __future__ import annotations

import glob
import os
from pathlib import Path

from . import core


def list_ssh_config_hosts(config_path: Path | None = None, seen: set[Path] | None = None) -> list[str]:
    config = config_path or (Path.home() / ".ssh" / "config")
    seen = seen or set()
    try:
        resolved = config.resolve()
    except OSError:
        resolved = config
    if resolved in seen or not config.exists():
        return []
    seen.add(resolved)

    hosts: list[str] = []
    for raw_line in config.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        words = line.split()
        if not words:
            continue
        keyword = words[0].lower()
        if keyword == "include":
            for pattern in words[1:]:
                expanded = os.path.expanduser(pattern)
                if not os.path.isabs(expanded):
                    expanded = str(config.parent / expanded)
                for included in glob.glob(expanded):
                    hosts.extend(list_ssh_config_hosts(Path(included), seen))
        elif keyword == "host":
            for host in words[1:]:
                if "*" not in host and "?" not in host and "!" not in host:
                    hosts.append(host)

    unique: list[str] = []
    for host in hosts:
        if host not in unique:
            unique.append(host)
    return unique


def _server_id(host_alias: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in host_alias)
    return f"sshcfg_{cleaned or 'host'}"


def resolved_ssh_config(host_alias: str) -> dict[str, list[str]]:
    return core.read_ssh_config(host_alias, None)


def live_server_for_host(host_alias: str) -> dict:
    config = resolved_ssh_config(host_alias)
    key_file = core.first_usable_path(config.get("identityfile", []), must_exist=True)
    return {
        "id": _server_id(host_alias),
        "name": host_alias,
        "mode": "ssh_config",
        "source": "ssh_config_live",
        "host_alias": host_alias,
        "host": core.first_ssh_value(config, "hostname", host_alias),
        "user": core.first_ssh_value(config, "user", ""),
        "port": core.first_ssh_value(config, "port", "22"),
        "auth": "key",
        "key_file": key_file,
        "remote_path": "",
        "mountpoint": "",
        "cache_mode": "",
    }


def live_servers() -> list[dict]:
    servers: list[dict] = []
    for host in list_ssh_config_hosts():
        try:
            servers.append(live_server_for_host(host))
        except Exception:
            servers.append(
                {
                    "id": _server_id(host),
                    "name": host,
                    "mode": "ssh_config",
                    "source": "ssh_config_live",
                    "host_alias": host,
                    "host": host,
                    "user": "",
                    "port": "22",
                    "auth": "key",
                    "key_file": "",
                    "remote_path": "",
                    "mountpoint": "",
                    "cache_mode": "",
                    "resolve_error": True,
                }
            )
    return servers


def detail_text(server: dict) -> str:
    host_alias = server.get("host_alias") or server.get("name") or ""
    lines = [f"Host {host_alias}", ""]
    try:
        config = resolved_ssh_config(host_alias)
    except Exception as exc:
        return "\n".join(lines + [f"Failed to resolve SSH config: {exc}"])

    keys = [
        "hostname",
        "user",
        "port",
        "identityfile",
        "identitiesonly",
        "proxyjump",
        "proxycommand",
        "userknownhostsfile",
        "serveraliveinterval",
        "serveralivecountmax",
        "controlmaster",
        "controlpath",
        "controlpersist",
    ]
    for key in keys:
        values = config.get(key, [])
        if values:
            lines.append(f"{key}: {', '.join(values)}")
    return "\n".join(lines)
