# AI Video Agent - Unified Startup Script
# Usage: .\scripts\startup\start.ps1 [mode]
# Modes: docker, local, check

param(
    [string]$Mode = "docker"
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  AI Video Agent - Startup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

if ($Mode -eq "check") {
    # Just check status
    Write-Host "Checking service status..." -ForegroundColor Yellow
    try {
        $services = docker-compose ps --format json 2>$null | ConvertFrom-Json
        $allRunning = $true
        
        foreach ($service in $services) {
            $status = if ($service.State -eq "running") { "[OK]" } else { "[STOPPED]" }
            $color = if ($service.State -eq "running") { "Green" } else { "Red" }
            Write-Host "   $status $($service.Service): $($service.State)" -ForegroundColor $color
            
            if ($service.State -ne "running") {
                $allRunning = $false
            }
        }
        
        Write-Host ""
        if ($allRunning) {
            Write-Host "[SUCCESS] All services are running!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Access:" -ForegroundColor Cyan
            Write-Host "  Web UI:  http://localhost:8000" -ForegroundColor White
            Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
        } else {
            Write-Host "[INFO] Some services stopped. Run: .\scripts\startup\start.ps1 docker" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] Docker not available or services not started" -ForegroundColor Red
        Write-Host "Run: .\scripts\startup\start.ps1 docker" -ForegroundColor Yellow
    }
    
} elseif ($Mode -eq "local") {
    # Local startup (no Docker)
    Write-Host "Starting in LOCAL mode (no Docker)..." -ForegroundColor Yellow
    Write-Host ""
    
    # Check Python
    try {
        python --version 2>&1 | Out-Null
        Write-Host "[OK] Python installed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Python not found" -ForegroundColor Red
        exit 1
    }
    
    # Check Redis
    Write-Host "Checking Redis..." -ForegroundColor Yellow
    try {
        $redisTest = redis-cli ping 2>&1
        if ($redisTest -eq "PONG") {
            Write-Host "[OK] Redis connected" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Redis not responding" -ForegroundColor Red
            Write-Host "Please start Redis first" -ForegroundColor Yellow
            exit 1
        }
    } catch {
        Write-Host "[ERROR] Redis not available" -ForegroundColor Red
        exit 1
    }
    
    # Install dependencies
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    
    # Start Celery workers
    Write-Host ""
    Write-Host "Starting Celery workers..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "celery -A tasks.celery_app worker --loglevel=info -Q download,analysis,generation,editing"
    
    # Start web server
    Write-Host ""
    Write-Host "Starting web server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn main:app --host 0.0.0.0 --port 8000"
    
    Write-Host ""
    Write-Host "[SUCCESS] Services started in separate windows!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access: http://localhost:8000" -ForegroundColor Cyan
    
} else {
    # Docker mode (default)
    Write-Host "Starting in DOCKER mode..." -ForegroundColor Yellow
    Write-Host ""
    
    # Check Docker
    try {
        docker --version 2>&1 | Out-Null
        Write-Host "[OK] Docker available" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Docker not found" -ForegroundColor Red
        exit 1
    }
    
    # Check if services are already running
    Write-Host "Checking existing services..." -ForegroundColor Yellow
    $running = docker-compose ps --format json 2>$null | ConvertFrom-Json | Where-Object { $_.State -eq "running" }
    
    if ($running.Count -gt 0) {
        Write-Host "[INFO] Some services already running" -ForegroundColor Yellow
        Write-Host "Stopping existing services..." -ForegroundColor Yellow
        docker-compose down
        Write-Host ""
    }
    
    # Start services
    Write-Host "Starting services..." -ForegroundColor Yellow
    docker-compose up -d
    
    Write-Host ""
    Write-Host "Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow
    for ($i = 30; $i -gt 0; $i--) {
        Write-Host "`r   Waiting... $i seconds remaining" -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""
    
    # Check status
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor Cyan
    docker-compose ps
    
    # Show logs
    Write-Host ""
    Write-Host "Recent Logs:" -ForegroundColor Cyan
    docker-compose logs --tail=20 web
    
    Write-Host ""
    Write-Host "[SUCCESS] All services started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access:" -ForegroundColor Cyan
    Write-Host "  Web UI:  http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Cyan
    Write-Host "  Check status: .\scripts\startup\start.ps1 check" -ForegroundColor Gray
    Write-Host "  View logs: docker-compose logs -f" -ForegroundColor Gray
    Write-Host "  Stop: docker-compose down" -ForegroundColor Gray
}
