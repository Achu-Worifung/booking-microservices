# PowerShell script to run all microservices
Write-Host "🚀 Starting all microservices..." -ForegroundColor Green
Write-Host "========================================"

# Function to start a service
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$Directory,
        [int]$Port
    )
    
    Write-Host "Starting $ServiceName on port $Port..." -ForegroundColor Yellow
    
    # Check if directory exists
    if (Test-Path $Directory) {
        Start-Process powershell -ArgumentList "-Command", "cd '$Directory'; python main.py" -WindowStyle Normal
        Start-Sleep -Seconds 1
    } else {
        Write-Host "❌ Directory '$Directory' not found!" -ForegroundColor Red
    }
}

# Start each microservice
Start-Service "Car Booking Service" "car-booking" 8001
Start-Service "Car Service" "car-service" 8010
Start-Service "Flight Booking Service" "flight-booking" 8002
Start-Service "Flight Service" "flight-service" 8003
Start-Service "Hotel Service" "hotel-service" 8020
Start-Service "User Service" "user-service" 8004
Start-Service "Trip Service" "trip-service" 8005

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host "========================================"
Write-Host "🚗 Car Booking Service:  http://localhost:8001" -ForegroundColor Cyan
Write-Host "🚙 Car Service:          http://localhost:8010" -ForegroundColor Cyan
Write-Host "✈️  Flight Booking:       http://localhost:8002" -ForegroundColor Cyan
Write-Host "🛫 Flight Service:       http://localhost:8003" -ForegroundColor Cyan
Write-Host "🏨 Hotel Service:        http://localhost:8020" -ForegroundColor Cyan
Write-Host "👤 User Service:         http://localhost:8004" -ForegroundColor Cyan
Write-Host "🗺️  Trip Service:         http://localhost:8005" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""
Write-Host "💡 Each service is running in its own window" -ForegroundColor Yellow
Write-Host "🔍 Check individual windows for service logs and errors" -ForegroundColor Yellow
Write-Host "⏹️  Close individual windows to stop services" -ForegroundColor Yellow

Write-Host ""
Write-Host "Press any key to exit this script (services will continue running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
