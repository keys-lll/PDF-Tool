param(
    [string]$Version = "1.1.1",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$bundleName = "PDF-Page-Merger"
$bundleDir = Join-Path $Root "dist\$bundleName"
$zipPath = Join-Path $Root "dist\PDF-Page-Merger-$Version-windows-x64.zip"
$entryScript = Join-Path $Root "main.py"
$iconPath = Join-Path $Root "assets\app_icon.ico"
$versionFile = Join-Path $Root "windows\version_info.txt"
$specPath = Join-Path $Root "build\pyinstaller"
$workPath = Join-Path $Root "build\pyinstaller-work"
$distPath = Join-Path $Root "dist"
$readmePath = Join-Path $Root "windows\README-Windows.txt"
$noticesPath = Join-Path $Root "THIRD_PARTY_NOTICES.md"

if (Test-Path $bundleDir) {
    Remove-Item $bundleDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $specPath | Out-Null
New-Item -ItemType Directory -Force -Path $workPath | Out-Null

Write-Host "Building $bundleName $Version with PyInstaller..."
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name $bundleName `
    --icon $iconPath `
    --version-file $versionFile `
    --collect-all pypdfium2 `
    --collect-all pypdfium2_raw `
    --specpath $specPath `
    --workpath $workPath `
    --distpath $distPath `
    $entryScript
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Copy-Item $readmePath (Join-Path $bundleDir "README-Windows.txt")
Copy-Item $noticesPath (Join-Path $bundleDir "THIRD_PARTY_NOTICES.md")

Write-Host "Creating $zipPath..."
Compress-Archive -Path $bundleDir -DestinationPath $zipPath -CompressionLevel Optimal
Write-Host "Built $zipPath"
