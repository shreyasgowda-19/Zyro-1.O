Write-Host "Resetting & Seeding PayGuard 360 demo database..." -ForegroundColor Cyan
python scripts/reset_demo.py

Write-Host "Starting Backend API on http://127.0.0.1:8000..." -ForegroundColor Green
$backend = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory "$PSScriptRoot\..\backend" -PassThru

Write-Host "Starting Frontend on http://localhost:5173..." -ForegroundColor Green
$frontend = Start-Process npm -ArgumentList "run", "dev" -WorkingDirectory "$PSScriptRoot\..\frontend" -PassThru

Write-Host "PayGuard 360 is running!" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop services." -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "Stopping services..." -ForegroundColor Red
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -ErrorAction SilentlyContinue
}
