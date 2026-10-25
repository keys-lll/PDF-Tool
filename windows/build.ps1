param(
    [string]$Version = "1.1.0",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$bundleName = "PDF-Page-Merger"
$bundleDir = Join-Path $Root "dist\$bundleName"
$zipPath = Join-Path $Root "dist\PDF-Page-Merger-$Version-windows-x64.zip"

if (Test-Path $bundleDir) {
    Remove-Item $bundleDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Force -Path "build\pyinstaller" | Out-Null
New-Item -ItemType Directory -Force -Path "build\pyinstaller-work" | Out-Null

Write-Host "Building $bundleName $Version with PyInstaller..."
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name $bundleName `
    --icon "assets\app_icon.ico" `
    --version-file "windows\version_info.txt" `
    --collect-all pypdfium2 `
    --collect-all pypdfium2_raw `
    --specpath "build\pyinstaller" `
    --workpath "build\pyinstaller-work" `
    --distpath "dist" `
    "main.py"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Copy-Item "windows\README-Windows.txt" (Join-Path $bundleDir "README-Windows.txt")
Copy-Item "THIRD_PARTY_NOTICES.md" (Join-Path $bundleDir "THIRD_PARTY_NOTICES.md")

Write-Host "Creating $zipPath..."
Compress-Archive -Path $bundleDir -DestinationPath $zipPath -CompressionLevel Optimal
Write-Host "Built $zipPath"
