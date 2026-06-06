$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Spec = Join-Path $RepoRoot "packaging\windows\spud-imprint.spec"
$DistDir = Join-Path $RepoRoot "dist\spud-imprint-windows-x64"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Push-Location $RepoRoot
try {
    & $Python -m unittest discover -s tests
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    & $Python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('PyInstaller') else 1)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller is not installed; installing it into the active environment with uv."
        & uv pip install pyinstaller
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    & $Python -m PyInstaller --noconfirm --clean $Spec
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    foreach ($Name in @("assets", "templates", "examples")) {
        $Source = Join-Path $RepoRoot $Name
        $Target = Join-Path $DistDir $Name
        if (Test-Path $Target) {
            Remove-Item -Recurse -Force $Target
        }
        Copy-Item -Recurse -Force $Source $Target
    }

    & $Python scripts\smoke-packaged-cli.py --dist-dir $DistDir
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "Windows package ready: $DistDir"
}
finally {
    Pop-Location
}
