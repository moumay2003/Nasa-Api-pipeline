#!/bin/bash

# This script installs Spark client in the Airflow container
# Run this script before executing the DAG

set -e

# Target Airflow container
CONTAINER_NAME="airflow-webserver"

echo "Installing Spark client in $CONTAINER_NAME..."

# Install Java
docker exec $CONTAINER_NAME apt-get update
docker exec $CONTAINER_NAME apt-get install -y openjdk-11-jdk wget

# Set JAVA_HOME
docker exec $CONTAINER_NAME bash -c 'echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> /home/airflow/.bashrc'

# Download and install Spark
SPARK_VERSION="3.3.0"
HADOOP_VERSION="3"

docker exec $CONTAINER_NAME wget -q -O /tmp/spark.tgz https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz
docker exec $CONTAINER_NAME mkdir -p /opt/spark
docker exec $CONTAINER_NAME tar -xzf /tmp/spark.tgz -C /opt/spark --strip-components=1
docker exec $CONTAINER_NAME rm /tmp/spark.tgz

# Set permissions
docker exec $CONTAINER_NAME chmod -R 755 /opt/spark

# Set environment variables
docker exec $CONTAINER_NAME bash -c 'echo "export SPARK_HOME=/opt/spark" >> /home/airflow/.bashrc'
docker exec $CONTAINER_NAME bash -c 'echo "export PATH=\$PATH:\$SPARK_HOME/bin" >> /home/airflow/.bashrc'
docker exec $CONTAINER_NAME bash -c 'echo "export PYTHONPATH=\$SPARK_HOME/python:\$SPARK_HOME/python/lib/py4j-0.10.9-src.zip:\$PYTHONPATH" >> /home/airflow/.bashrc'

# Create SPARK_MASTER_URL environment variable
docker exec $CONTAINER_NAME bash -c 'echo "export SPARK_MASTER_URL=spark://spark-master:7077" >> /home/airflow/.bashrc'

echo "✅ Spark client installation complete!"
echo "Run the following command to test the connection:"
echo "docker exec $CONTAINER_NAME /opt/spark/bin/spark-submit --master spark://spark-master:7077 --version"
