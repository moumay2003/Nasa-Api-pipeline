#!/bin/bash
# Setup Airflow connections for Spark cluster

echo "🔧 Setting up Airflow connections..."

# Wait for Airflow to be ready
echo "Waiting for Airflow webserver to be ready..."
until docker exec airflow-webserver airflow version > /dev/null 2>&1; do
  echo "Waiting for Airflow..."
  sleep 5
done

# Create Spark connection
echo "Creating Spark connection..."
docker exec airflow-webserver airflow connections add \
  --conn-id spark_cluster \
  --conn-type spark \
  --conn-host spark-master \
  --conn-port 7077 \
  --conn-extra '{"spark-home": "/opt/spark", "java-home": "/usr/lib/jvm/java-17-openjdk-amd64"}'

echo "✅ Spark connection created successfully!"

# Verify connection
echo "Verifying connections..."
docker exec airflow-webserver airflow connections list | grep spark_cluster

echo "🎉 Setup complete!"