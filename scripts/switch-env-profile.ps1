param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("local", "production")]
    [string]$Profile,

    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Path $PSScriptRoot -Parent
$envPath = Join-Path $repoRoot ".env"

switch ($Profile) {
    "local" { $templatePath = Join-Path $repoRoot ".env.local.example" }
    "production" { $templatePath = Join-Path $repoRoot ".env.production.example" }
    default { throw "Unsupported profile: $Profile" }
}

if (-not (Test-Path -Path $templatePath)) {
    throw "Template not found: $templatePath"
}

if ((Test-Path -Path $envPath) -and -not $Force) {
    Write-Host "Refusing to overwrite existing .env without -Force." -ForegroundColor Yellow
    Write-Host "Target: $envPath"
    Write-Host "Template: $templatePath"
    Write-Host "Run again with -Force to overwrite."
    exit 1
}

Copy-Item -Path $templatePath -Destination $envPath -Force

Write-Host "Switched .env to profile: $Profile" -ForegroundColor Green
Write-Host "Source template: $templatePath"
Write-Host "Target file: $envPath"
Write-Host "Next step: fill placeholders in .env before running the app."
