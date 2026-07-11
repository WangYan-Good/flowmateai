[CmdletBinding()]
param(
    [ValidateSet("Start", "Test")]
    [string]$Action = "Start",

    [ValidateSet("Company", "DeepSeek", "Qwen")]
    [string]$Provider = "Company"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Resolve-Python {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "python was not found in PATH. Activate your Conda environment first, for example: conda activate flowmate."
    }

    & python -c "import sys; assert sys.version_info >= (3, 11)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "The active Python is lower than 3.11. Activate a Conda environment with Python 3.11+, for example: conda activate flowmate."
    }

    return "python"
}

if (-not (Test-Path -LiteralPath ".env")) {
    $profileFile = switch ($Provider) {
        "DeepSeek" { ".env.deepseek.example" }
        "Qwen" { ".env.qwen.example" }
        default { ".env.example" }
    }
    $content = Get-Content -LiteralPath $profileFile -Raw
    if ($Provider -eq "Company") {
        $content = $content.Replace("http://host.docker.internal:8001/v1", "http://127.0.0.1:8001/v1")
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $PSScriptRoot ".env"),
        $content,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host "Created .env from $profileFile." -ForegroundColor Yellow
    Write-Host "Before a real demo, set Microsoft credentials and verify LLM_BASE_URL in .env." -ForegroundColor Yellow
}

$envContent = Get-Content -LiteralPath ".env" -Raw
if ($Action -eq "Start" -and $envContent -match '(?m)^LLM_API_KEY=replace-with-') {
    throw "Edit .env and replace LLM_API_KEY with your official API key, then run this script again."
}

if (-not $env:CONDA_PREFIX) {
    throw "No active Conda environment detected. Run 'conda activate flowmate' first, then run this script again."
}

$python = Resolve-Python
$activeCondaEnv = if ($env:CONDA_DEFAULT_ENV) { $env:CONDA_DEFAULT_ENV } else { $env:CONDA_PREFIX }
Write-Host "Using active Conda environment: $activeCondaEnv" -ForegroundColor Cyan

Write-Host "Installing/updating dependencies in current environment..." -ForegroundColor Cyan
& $python -m pip install --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

if ($Action -eq "Test") {
    & $python -m unittest discover -s tests -v
    exit $LASTEXITCODE
}

$port = 8000
$portLine = Get-Content -LiteralPath ".env" | Where-Object { $_ -match '^PORT=\d+$' } | Select-Object -Last 1
if ($portLine) {
    $port = [int]($portLine -replace '^PORT=', '')
}

Write-Host "Starting FlowMate at http://localhost:$port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
& $python -m uvicorn backend.main:app --host 0.0.0.0 --port $port
exit $LASTEXITCODE
