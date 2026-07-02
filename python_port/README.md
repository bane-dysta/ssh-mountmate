# SSH MountMate Python Port

This directory is an experimental cross-platform Python rewrite of the SSH
MountMate GUI. It intentionally lives outside the current `app/` implementation
so the production Windows package can stay stable while this port evolves.

## Goals

- Keep the user-visible behavior close to the existing GUI.
- Share one Python codebase across Windows, macOS, and Linux.
- Keep rclone as the mount engine instead of reimplementing SFTP/VFS/FUSE.
- Prefer installed or bundled rclone, and keep download/install behavior behind
  a platform-specific dependency layer.
- Build native artifacts per platform.

## Packaging Reality

Python applications can be packaged as double-clickable executables, but the
artifacts are platform-specific. PyInstaller and similar tools generally build
for the host platform, so practical "cross-platform builds" should use:

- Windows runner -> `.exe`
- macOS runner -> `.app` or executable
- Linux runner -> executable/AppImage/tarball

This port therefore treats GitHub Actions or per-platform build machines as the
normal release path rather than relying on true cross-compilation from one OS.

## rclone Strategy

The intended rclone lookup order is:

1. User-configured rclone path.
2. Bundled rclone under the app resources directory.
3. Extracted managed rclone under the per-user data directory.
4. `PATH`.
5. Platform installer or downloader.

For future installer/download behavior, prefer `downloads.rclone.org` over
GitHub release URLs when a direct download is needed. WinFsp/macFUSE/FUSE remain
system dependencies because they provide OS-level filesystem support.

Manual rclone install commands can be printed with:

```bash
python -m ssh_mountmate --install-help
```

Current guidance:

```text
Windows:
  winget install --id Rclone.Rclone -e
  Download and unzip: https://downloads.rclone.org/rclone-current-windows-amd64.zip
  Place rclone.exe on PATH or next to SSHMountMate.exe.

macOS:
  brew install rclone
  or: curl https://rclone.org/install.sh | sudo bash
  Manual zip: https://downloads.rclone.org/rclone-current-osx-amd64.zip

Linux:
  curl https://rclone.org/install.sh | sudo bash
  or use your distro package manager, for example: sudo apt install rclone
  Manual zip: https://downloads.rclone.org/rclone-current-linux-amd64.zip
```

## Local Development

```bash
cd python_port
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m ssh_mountmate
```

## Local Build

```bash
python build/build_local.py
```

The build script expects PyInstaller to be installed in the active environment.
It only builds for the current OS.
