[CmdletBinding()]
param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

$dashboardPath = Join-Path $PSScriptRoot 'dashboard'
$indexPath = Join-Path $dashboardPath 'index.html'

if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
    throw "Dashboard entry file not found: $indexPath"
}

$pythonCandidates = @(
    (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
    (Join-Path (Split-Path -Parent $PSScriptRoot) '.venv\Scripts\python.exe')
)

$pythonPath = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $pythonPath) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonPath = $pythonCommand.Source
    }
}

if (-not $pythonPath) {
    throw 'Python was not found. Install Python or activate the project virtual environment.'
}

Write-Host "Serving P3 Network Assurance from $dashboardPath"
Write-Host "Open http://localhost:$Port/"

& $pythonPath -m http.server $Port --directory $dashboardPath
