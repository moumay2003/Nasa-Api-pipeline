# Distributed Spark Configuration Guide 🌟

## 🎯 Overview

Your NASA NEO pipeline is now configured to use a **distributed Apache Spark cluster** with:
- **1 Spark Master** container (`spark-master`)
- **2 Spark Worker** containers (`spark-worker`, `spark-worker-2`)
- **Airflow** connecting to the cluster for data processing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Spark Master  │    │  Spark Worker 1 │    │  Spark Worker 2 │
│   (Coordinator) │◄───┤  (2 cores, 2GB) │    │  (2 cores, 2GB) │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲
         │ spark://spark-master:7077
         │
┌─────────────────┐
│    Airflow      │
│   (NASA NEO     │
│    Pipeline)    │
└─────────────────┘
```

## ⚙️ Configuration Details

### Spark Master
- **Image**: `apache/spark:3.4.1`
- **Ports**: 
  - `8088:8080` (Web UI)
  - `7077:7077` (Master Port)
- **URL**: `spark://spark-master:7077`

### Spark Workers (2x)
- **Cores per Worker**: 2
- **Memory per Worker**: 2GB
- **Total Cluster Capacity**: 4 cores, 4GB RAM
- **Worker UIs**: 
  - Worker 1: `localhost:8081`
  - Worker 2: `localhost:8082`

## 🚀 Quick Start

### 1. Start the Cluster
```bash
cd "c:\Users\mouad\OneDrive - um5.ac.ma\Desktop\airlow_innovx - Copy"

# Start all services (Spark cluster + Airflow + MySQL)
docker-compose up -d

# Check service status
docker-compose ps
```

### 2. Verify Spark Cluster
```bash
# Run the verification script
python verify_spark_cluster.py
```

### 3. Access Web UIs
- **Spark Master UI**: http://localhost:8088
- **Spark Worker 1 UI**: http://localhost:8081  
- **Spark Worker 2 UI**: http://localhost:8082
- **Airflow UI**: http://localhost:8080

### 4. Configure Airflow Connections
```powershell
# Windows PowerShell
.\setup_airflow_connections.ps1
```

## 🔧 Configuration Changes Made

### 1. Docker Compose Updates
```yaml
# Enhanced Spark Worker Configuration
spark-worker:
  environment:
    - SPARK_WORKER_CORES=2
    - SPARK_WORKER_MEMORY=2g
    - SPARK_WORKER_PORT=8881
    - SPARK_WORKER_WEBUI_PORT=8081

spark-worker-2:
  environment:
    - SPARK_WORKER_CORES=2
    - SPARK_WORKER_MEMORY=2g
    - SPARK_WORKER_PORT=8882
    - SPARK_WORKER_WEBUI_PORT=8081
```

### 2. Airflow DAG Configuration
```python
# Distributed Spark Session
spark = SparkSession.builder \
    .appName("nasa_neo_etl_distributed") \
    .master("spark://spark-master:7077") \  # Connect to cluster
    .config("spark.executor.memory", "1800m") \
    .config("spark.executor.cores", "2") \
    .config("spark.cores.max", "4") \       # Use all available cores
    .getOrCreate()
```

## 📊 Monitoring & Verification

### Check Cluster Status
```bash
# Check running containers
docker-compose ps

# View Spark master logs
docker-compose logs spark-master

# View worker logs  
docker-compose logs spark-worker
docker-compose logs spark-worker-2
```

### Spark Web UI Monitoring
1. **Master UI** (http://localhost:8088):
   - Workers status
   - Running applications
   - Cluster resources

2. **Worker UIs** (http://localhost:8081, 8082):
   - Executor details
   - Task execution
   - Resource utilization

### Application Monitoring
```python
# In your Spark application
spark_context = spark.sparkContext
print(f"Application ID: {spark_context.applicationId}")
print(f"Default Parallelism: {spark_context.defaultParallelism}")
print(f"Available Cores: {spark_context._jsc.sc().statusTracker().getExecutorInfos()}")
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Workers Not Connecting
```bash
# Check network connectivity
docker-compose exec spark-worker ping spark-master

# Restart workers
docker-compose restart spark-worker spark-worker-2
```

#### 2. Memory Issues
```bash
# Check container resources
docker stats

# Increase worker memory in docker-compose.yaml
environment:
  - SPARK_WORKER_MEMORY=3g  # Increase if needed
```

#### 3. Port Conflicts
```bash
# Check port usage
netstat -an | findstr "7077\|8080\|8081\|8082"

# Change ports in docker-compose.yaml if needed
```

#### 4. Driver Connection Issues
```python
# Add these configs to Spark session
.config("spark.driver.host", socket.gethostname())
.config("spark.driver.bindAddress", "0.0.0.0")
.config("spark.network.timeout", "600s")
```

### Log Analysis
```bash
# Detailed Spark master logs
docker-compose logs -f spark-master | grep ERROR

# Worker connection logs
docker-compose logs -f spark-worker | grep "Connected to"

# Airflow task logs
docker-compose logs -f airflow-worker | grep spark
```

## 🎯 Performance Optimization

### 1. Resource Allocation
```yaml
# Optimize based on your system
spark-worker:
  environment:
    - SPARK_WORKER_CORES=4      # Increase for more powerful machines
    - SPARK_WORKER_MEMORY=4g    # Adjust based on available RAM
```

### 2. Spark Configuration Tuning
```python
# In your Spark session
.config("spark.sql.adaptive.enabled", "true")
.config("spark.sql.adaptive.coalescePartitions.enabled", "true")
.config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB")
.config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

### 3. Data Partitioning
```python
# Optimal partitioning for your cluster
df = df.repartition(4)  # Match your total cores (2 workers × 2 cores)
```

## 📈 Production Considerations

### 1. High Availability
- Use external Spark cluster (Kubernetes, Standalone)
- Configure Spark with persistent storage
- Implement health checks and auto-restart

### 2. Security
```python
# Add authentication if needed
.config("spark.authenticate", "true")
.config("spark.authenticate.secret", "your-secret")
```

### 3. Monitoring
- Set up Spark History Server
- Configure metrics collection
- Use Prometheus/Grafana for monitoring

## 🎉 Benefits of Distributed Setup

✅ **Parallel Processing**: Work distributed across 2 workers
✅ **Scalability**: Easy to add more workers  
✅ **Fault Tolerance**: Worker failure doesn't stop processing
✅ **Resource Isolation**: Better resource management
✅ **Performance**: 4 cores available vs 1 in local mode
✅ **Production Ready**: Mimics real-world Spark deployments

Your NASA NEO pipeline is now ready to process data using the full power of your distributed Spark cluster! 🚀