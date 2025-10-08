# NASA NEO Pipeline - Complete Setup Script
# This script sets up the entire environment with proper Spark-Airflow integration

Write-Host "🚀 NASA NEO Pipeline Setup" -ForegroundColor Blue
Write-Host "=" * 50 -ForegroundColor Blue

# Step 1: Stop existing containers
Write-Host "Step 1: Stopping existing containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Step 2: Clean up old images (optional - uncomment if needed)
# Write-Host "Step 2: Cleaning up old images..." -ForegroundColor Yellow
# docker image prune -f

# Step 3: Build new images
Write-Host "Step 3: Building Docker images..." -ForegroundColor Yellow
Write-Host "Building Airflow image..." -ForegroundColor Cyan
docker-compose build airflow-webserver
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Airflow image build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Building Spark images..." -ForegroundColor Cyan
docker-compose build spark-master
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Spark image build failed!" -ForegroundColor Red
    exit 1
}

# Step 4: Start the services
Write-Host "Step 4: Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Step 5: Wait for services to be ready
Write-Host "Step 5: Waiting for services to initialize..." -ForegroundColor Yellow
Write-Host "This may take 2-3 minutes..." -ForegroundColor Cyan

Start-Sleep -Seconds 30

# Check service status
Write-Host "Checking service status..." -ForegroundColor Cyan
docker-compose ps

# Step 6: Setup Airflow connections
Write-Host "Step 6: Setting up Airflow connections..." -ForegroundColor Yellow
Start-Sleep -Seconds 30  # Wait a bit more for Airflow to be fully ready

& "$PSScriptRoot\setup_connections.ps1"

# Step 7: Verify Spark cluster
Write-Host "Step 7: Verifying Spark cluster..." -ForegroundColor Yellow
docker exec spark-master /opt/spark/bin/spark-shell --version 2>&1 | Select-String "version"

# Step 8: Test connectivity
Write-Host "Step 8: Testing connectivity..." -ForegroundColor Yellow
Write-Host "Running connectivity test..." -ForegroundColor Cyan
docker exec airflow-webserver python /opt/airflow/test_spark_connectivity.py

Write-Host "`n🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green
Write-Host "Access points:" -ForegroundColor White
Write-Host "• Airflow UI: http://localhost:8080 (admin/admin)" -ForegroundColor Cyan
Write-Host "• Spark Master UI: http://localhost:8088" -ForegroundColor Cyan
Write-Host "• Spark Worker 1: http://localhost:8081" -ForegroundColor Cyan
Write-Host "• Spark Worker 2: http://localhost:8082" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Go to Airflow UI and enable the 'nasa_neo_pipeline' DAG" -ForegroundColor Cyan
Write-Host "2. Trigger a manual run to test the pipeline" -ForegroundColor Cyan
Write-Host "3. Check logs in both Airflow and Spark UIs" -ForegroundColor Cyan