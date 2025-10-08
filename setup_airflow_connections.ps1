# Airflow MySQL Connection Setup Script for Windows PowerShell
# Run this after starting your Airflow containers

Write-Host "🔧 Setting up Airflow MySQL connection..." -ForegroundColor Green

# Wait for Airflow to be ready
Start-Sleep -Seconds 10

# Add MySQL connection to Airflow
Write-Host "📡 Adding MySQL connection..." -ForegroundColor Yellow
docker-compose exec airflow-webserver airflow connections add `
    --conn-id mysql_default `
    --conn-type mysql `
    --conn-host mysql `
    --conn-login airflow `
    --conn-password airflow `
    --conn-schema airflow `
    --conn-port 3306

# Add Spark connection to Airflow
Write-Host "🔥 Adding Spark connection..." -ForegroundColor Yellow
docker-compose exec airflow-webserver airflow connections add `
    --conn-id spark_default `
    --conn-type spark `
    --conn-host spark-master `
    --conn-port 7077

# Set NASA API Key as Airflow variable (optional)
Write-Host "🔑 Setting NASA API Key..." -ForegroundColor Yellow
docker-compose exec airflow-webserver airflow variables set `
    NASA_API_KEY "3NcI1W7rKoehu3KEtqGFjh4nwV6nuO6v7a3WhYrC"

Write-Host "✅ Airflow connections configured successfully!" -ForegroundColor Green
Write-Host "📊 Access Airflow UI at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🔑 Username: airflow, Password: airflow" -ForegroundColor Cyan