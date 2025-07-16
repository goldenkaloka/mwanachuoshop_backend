# Docker Cleanup Script for Windows
# Run this script after restarting Docker Desktop

Write-Host "Starting Docker cleanup..." -ForegroundColor Green

# Stop all containers
Write-Host "Stopping all containers..." -ForegroundColor Yellow
docker-compose down 2>$null

# Remove all containers
Write-Host "Removing all containers..." -ForegroundColor Yellow
docker container prune -f 2>$null

# Remove all images
Write-Host "Removing all images..." -ForegroundColor Yellow
docker image prune -a -f 2>$null

# Remove all volumes
Write-Host "Removing all volumes..." -ForegroundColor Yellow
docker volume prune -f 2>$null

# Remove all networks
Write-Host "Removing all networks..." -ForegroundColor Yellow
docker network prune -f 2>$null

# Complete system cleanup
Write-Host "Performing complete system cleanup..." -ForegroundColor Yellow
docker system prune -a -f --volumes 2>$null

Write-Host "Cleanup completed!" -ForegroundColor Green
Write-Host "Now run: docker-compose build --no-cache" -ForegroundColor Cyan
Write-Host "Then run: docker-compose up -d" -ForegroundColor Cyan 