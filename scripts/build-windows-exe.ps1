$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dist = Join-Path $Root "dist\SSHMountMate-win"

python -m pip install --upgrade pyinstaller pystray pillow

pyinstaller `
  --noconsole `
  --name SSHMountMate `
  --distpath $Dist `
  --workpath (Join-Path $Root "build\pyinstaller") `
  --specpath (Join-Path $Root "build") `
  --add-data "$Root\rsshmount.py;." `
  --hidden-import pystray._win32 `
  "$Root\rsshmount_gui.pyw"

Write-Host "built: $(Join-Path $Dist 'SSHMountMate\SSHMountMate.exe')"
