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
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -c "import sys; assert sys.version_info >= (3, 11)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Command = "py"; Prefix = @("-3.11") }
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; assert sys.version_info >= (3, 11)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Command = "python"; Prefix = @() }
        }
    }

    throw "Python 3.11 or newer was not found. Install it from https://www.python.org/downloads/windows/ and enable 'Add Python to PATH'."
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

$python = Resolve-Python
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating local Python virtual environment..." -ForegroundColor Cyan
    $createArgs = @($python.Prefix) + @("-m", "venv", ".venv")
    & $python.Command @createArgs
    if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv." }
}

Write-Host "Installing/updating dependencies in .venv..." -ForegroundColor Cyan
& $venvPython -m pip install --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

if ($Action -eq "Test") {
    & $venvPython -m unittest discover -s tests -v
    exit $LASTEXITCODE
}

$port = 8000
$portLine = Get-Content -LiteralPath ".env" | Where-Object { $_ -match '^PORT=\d+$' } | Select-Object -Last 1
if ($portLine) {
    $port = [int]($portLine -replace '^PORT=', '')
}

Write-Host "Starting FlowMate at http://localhost:$port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
& $venvPython -m uvicorn backend.main:app --host 0.0.0.0 --port $port
exit $LASTEXITCODE
