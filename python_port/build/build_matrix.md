# Build Matrix Plan

True cross-compilation is not the primary plan for this port. Build the same
source on each target platform instead.

| Target | Builder | Expected artifact |
| --- | --- | --- |
| Windows x64 | `windows-latest` | `SSHMountMate.exe` |
| macOS arm64/x64 | `macos-latest` | `SSHMountMate` or `.app` bundle |
| Linux x64 | `ubuntu-latest` | `SSHMountMate` tarball/AppImage candidate |

Future CI can install `.[build]` and run:

```bash
python python_port/build/build_local.py
```

The rclone binary can later be placed under a resource directory or downloaded
from `downloads.rclone.org` into a managed per-user bin directory.
