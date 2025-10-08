# Update Environment Script - Fixes Python Version Mismatch
# This script rebuilds containers with Python 3.10.8 consistency

Write-Host "🔧 NASA NEO Pipeline Environment Update" -ForegroundColor Green
Write-Host "Fixing Python version mismatch between Airflow and Spark workers" -ForegroundColor Yellow
Write-Host "=" * 60

# Step 1: Stop existing containers
Write-Host "`n📥 Stopping existing containers..." -ForegroundColor Cyan
docker-compose down

# Step 2: Remove old images to force rebuild
Write-Host "`n🗑️ Removing old images..." -ForegroundColor Cyan
docker image rm extending_airflow:latest -f 2>$null
docker image rm apache/spark:3.4.1 -f 2>$null

# Step 3: Pull the new Spark image
Write-Host "`n📦 Pulling new Spark image with Java 17..." -ForegroundColor Cyan
docker pull apache/spark:3.5.7-java17

# Step 4: Build new Airflow image with Python 3.10
Write-Host "`n🔨 Building new Airflow image with Python 3.10..." -ForegroundColor Cyan
docker-compose build --no-cache

# Step 5: Start all services
Write-Host "`n🚀 Starting updated services..." -ForegroundColor Cyan
docker-compose up -d

# Step 6: Wait for services to be ready
Write-Host "`n⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 7: Setup Airflow connections
Write-Host "`n🔗 Setting up Airflow connections..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

try {
    # Add MySQL connection
    docker-compose exec -T airflow-webserver airflow connections add `
        --conn-id mysql_default `
        --conn-type mysql `
        --conn-host mysql `
        --conn-login airflow `
        --conn-password airflow `
        --conn-schema airflow `
        --conn-port 3306

    # Set NASA API Key
    docker-compose exec -T airflow-webserver airflow variables set `
        NASA_API_KEY "3NcI1W7rKoehu3KEtqGFjh4nwV6nuO6v7a3WhYrC"

    Write-Host "✅ Connections configured successfully!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Connection setup failed. You may need to configure manually." -ForegroundColor Yellow
}

# Step 8: Verify Python versions
Write-Host "`n🐍 Verifying Python versions..." -ForegroundColor Cyan

Write-Host "Airflow containers Python version:" -ForegroundColor White
docker-compose exec -T airflow-webserver python --version

Write-Host "Spark Master Python version:" -ForegroundColor White
try {
    docker-compose exec -T spark-master python3.10 --version
} catch {
    docker-compose exec -T spark-master python3 --version
}

# Step 9: Display access information
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "🎉 UPDATE COMPLETED!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

Write-Host "`n📊 Access Information:" -ForegroundColor Cyan
Write-Host "• Airflow UI: http://localhost:8080 (airflow/airflow)" -ForegroundColor White
Write-Host "• Spark Master UI: http://localhost:8088" -ForegroundColor White
Write-Host "• Spark Worker 1 UI: http://localhost:8081" -ForegroundColor White
Write-Host "• Spark Worker 2 UI: http://localhost:8082" -ForegroundColor White

Write-Host "`n🔍 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for all services to fully initialize" -ForegroundColor White
Write-Host "2. Access Airflow UI and enable the 'nasa_neo_pipeline' DAG" -ForegroundColor White
Write-Host "3. Run: python verify_spark_cluster.py (to test Spark cluster)" -ForegroundColor White
Write-Host "4. Check container logs if needed: docker-compose logs [service-name]" -ForegroundColor White

Write-Host "`n🐍 Python Version Consistency:" -ForegroundColor Magenta
Write-Host "• All containers now use Python 3.10" -ForegroundColor White
Write-Host "• Spark version: 3.5.7 with Java 17" -ForegroundColor White
Write-Host "• PySpark version: 3.5.7 (matching Spark cluster)" -ForegroundColor White