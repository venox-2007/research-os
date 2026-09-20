# ResearchOS — Run React/Vite Frontend Server
Write-Host "Starting ResearchOS Frontend..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\..\frontend"
& "npm.cmd" run dev
