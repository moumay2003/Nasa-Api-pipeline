# Setup Airflow connections for Spark cluster
Write-Host "🔧 Setting up Airflow connections..." -ForegroundColor Blue

# Wait for Airflow to be ready
Write-Host "Waiting for Airflow webserver to be ready..." -ForegroundColor Yellow
do {
    try {
        docker exec airflow-webserver airflow version 2>$null | Out-Null
        $ready = $true
    } catch {
        Write-Host "Waiting for Airflow..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        $ready = $false
    }
} while (-not $ready)

# Create Spark connection
Write-Host "Creating Spark connection..." -ForegroundColor Yellow
docker exec airflow-webserver airflow connections add `
  --conn-id spark_cluster `
  --conn-type spark `
  --conn-host spark-master `
  --conn-port 7077 `
  --conn-extra '{\"spark-home\": \"/opt/spark\", \"java-home\": \"/usr/lib/jvm/java-17-openjdk-amd64\"}'

Write-Host "✅ Spark connection created successfully!" -ForegroundColor Green

# Verify connection
Write-Host "Verifying connections..." -ForegroundColor Yellow
docker exec airflow-webserver airflow connections list | Select-String "spark_cluster"

Write-Host "🎉 Setup complete!" -ForegroundColor Green