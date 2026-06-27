param(
    [string]$PythonPath = "python",
    [string]$VenvDir = "",
    [switch]$SkipInstall,
    [switch]$SkipModel
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ProjectRoot

if ([string]::IsNullOrWhiteSpace($VenvDir)) {
    # Keep the virtual environment in an ASCII path. Python venv launchers can
    # fail on some Windows machines when the venv itself lives under Chinese paths.
    $VenvDir = Join-Path $WorkspaceRoot ".image_algo_venv"
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Set-Location $ProjectRoot
$env:PYTHONUTF8 = "1"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    & $PythonPath -m venv $VenvDir
}

if (-not $SkipInstall) {
    Write-Host "Installing Python dependencies..."
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
}

if (-not $SkipModel) {
    Write-Host "Downloading YOLOv8n model if needed..."
    & $VenvPython (Join-Path $ProjectRoot "main.py") --download-model-only
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "1. Copy .env.example to .env and set MySQL password."
Write-Host "2. Put test images into images/."
Write-Host "3. Run: $VenvPython main.py"
