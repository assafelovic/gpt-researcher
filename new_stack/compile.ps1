# PowerShell script to compile TypeScript to JavaScript
# This works on Windows with tsc installed

$thisFilePath = $PSScriptRoot

# Ensure the output directory exists
if (-not (Test-Path -Path "$thisFilePath/static/js")) {
    New-Item -ItemType Directory -Path "$thisFilePath/static/js" -Force
}

# Compile TypeScript to JavaScript
tsc -p $thisFilePath/tsconfig.json

Write-Host "TypeScript compilation complete. Output in static/js directory."
