#!/bin/bash
# Airflow MySQL Connection Setup Script
# Run this after starting your Airflow containers

echo "🔧 Setting up Airflow MySQL connection..."

# Wait for Airflow to be ready
sleep 10

# Add MySQL connection to Airflow
docker-compose exec airflow-webserver airflow connections add \
    --conn-id mysql_default \
    --conn-type mysql \
    --conn-host mysql \
    --conn-login airflow \
    --conn-password airflow \
    --conn-schema airflow \
    --conn-port 3306

# Set NASA API Key as Airflow variable (optional)
docker-compose exec airflow-webserver airflow variables set \
    NASA_API_KEY "3NcI1W7rKoehu3KEtqGFjh4nwV6nuO6v7a3WhYrC"

echo "✅ Airflow connections configured successfully!"
echo "📊 Access Airflow UI at: http://localhost:8080"
echo "🔑 Username: airflow, Password: airflow"