$ErrorActionPreference = "Stop"

function Test-WinFsp {
    $paths = @(
        (Join-Path ${env:ProgramFiles(x86)} "WinFsp"),
        (Join-Path $env:ProgramFiles "WinFsp")
    )
    foreach ($path in $paths) {
        if ($path -and (Test-Path $path)) {
            return $true
        }
    }
    return $false
}

if (Test-WinFsp) {
    Write-Host "WinFsp is already installed."
    exit 0
}

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Installing WinFsp with winget..."
    winget install --id WinFsp.WinFsp -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0 -and (Test-WinFsp)) {
        exit 0
    }
    Write-Warning "winget did not complete WinFsp installation; trying next method."
}

if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "Installing WinFsp with Chocolatey..."
    choco install winfsp -y
    if ($LASTEXITCODE -eq 0 -and (Test-WinFsp)) {
        exit 0
    }
    Write-Warning "Chocolatey did not complete WinFsp installation; trying direct download."
}

Write-Host "Downloading latest WinFsp installer from GitHub..."
$release = Invoke-RestMethod "https://api.github.com/repos/winfsp/winfsp/releases/latest"
$asset = $release.assets |
    Where-Object { $_.name -match "^winfsp-.*\.msi$" -and $_.name -notmatch "symbols" } |
    Select-Object -First 1

if (-not $asset) {
    throw "Could not find a WinFsp MSI asset in the latest GitHub release."
}

$installer = Join-Path $env:TEMP $asset.name
Invoke-WebRequest $asset.browser_download_url -OutFile $installer

Write-Host "Starting WinFsp installer. Approve the UAC prompt if Windows asks."
$args = "/i `"$installer`" /qn /norestart"
$process = Start-Process msiexec.exe -ArgumentList $args -Wait -PassThru -Verb RunAs

if ($process.ExitCode -ne 0) {
    throw "WinFsp installer failed with exit code $($process.ExitCode)."
}

if (Test-WinFsp) {
    Write-Host "WinFsp installed."
    exit 0
}

throw "WinFsp installation finished but WinFsp was not detected. Reopen the terminal or reboot, then run rsshmount.cmd doctor."
