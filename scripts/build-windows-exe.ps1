$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dist = Join-Path $Root "dist\RSSHMount-win"
$BuildBin = Join-Path $Root "build\rclone-win\bin"
$Rclone = Join-Path $BuildBin "rclone.exe"

if (-not (Test-Path $Rclone)) {
  New-Item -ItemType Directory -Force -Path $BuildBin | Out-Null
  $Zip = Join-Path $env:TEMP "rclone-current-windows-amd64.zip"
  $Unpack = Join-Path $env:TEMP "rclone-current-windows-amd64"
  if (Test-Path $Unpack) {
    Remove-Item -Recurse -Force $Unpack
  }
  Invoke-WebRequest "https://downloads.rclone.org/rclone-current-windows-amd64.zip" -OutFile $Zip
  Expand-Archive $Zip -DestinationPath $Unpack -Force
  $Found = Get-ChildItem $Unpack -Recurse -Filter rclone.exe | Select-Object -First 1
  if (-not $Found) {
    throw "Could not find rclone.exe in downloaded archive."
  }
  Copy-Item $Found.FullName $Rclone -Force
}

python -m pip install --upgrade pyinstaller pystray pillow

pyinstaller `
  --noconsole `
  --name RSSHMount `
  --distpath $Dist `
  --workpath (Join-Path $Root "build\pyinstaller") `
  --specpath (Join-Path $Root "build") `
  --add-data "$Root\rsshmount.py;." `
  --add-data "$Root\install-windows-deps.ps1;." `
  --add-binary "$Rclone;bin" `
  --hidden-import pystray._win32 `
  "$Root\rsshmount_gui.pyw"

Write-Host "built: $(Join-Path $Dist 'RSSHMount\RSSHMount.exe')"
