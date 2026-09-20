# ResearchOS — Run FastAPI Backend Server
Write-Host "Starting ResearchOS Backend Server..." -ForegroundColor Cyan
python -m uvicorn backend.core.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
