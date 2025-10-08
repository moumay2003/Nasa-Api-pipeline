# NASA NEO Data Pipeline 🚀

An automated data pipeline for extracting, processing, and storing NASA Near-Earth Objects (NEO) data using Apache Airflow, Apache Spark, and MySQL.

## 🎯 Overview

This project implements a complete ETL pipeline that:
- **Extracts** NASA NEO data from the official API every 7 days
- **Processes** complex nested JSON data using Apache Spark
- **Stores** cleaned data in a MySQL database
- **Automates** the entire workflow using Apache Airflow

## 📊 Architecture

```
NASA API → Apache Spark → MySQL Database
    ↓           ↓              ↓
Data Extract → Process → Store → Schedule (Airflow)
```

## 🛠️ Components

- **Apache Airflow**: Workflow orchestration and scheduling
- **Apache Spark Cluster**: Distributed data processing (1 Master + 2 Workers)
- **MySQL**: Data storage and querying
- **Docker**: Containerized deployment
- **Python**: Data processing logic

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Python 3.10.8 (for consistent version across all containers)
- NASA API Key (free registration at https://api.nasa.gov/)

### 1. Start the Environment (Updated for Python 3.10 Consistency)
```bash
# For first-time setup or after Python version updates
.\update_environment.ps1  # Windows PowerShell (recommended)
# OR manually:
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for services to initialize (2-3 minutes)
docker-compose logs -f airflow-webserver
```

### 2. Validate Python Versions (New!)
```bash
# Verify all containers use Python 3.10 consistently
python validate_python_versions.py
```

### 3. Configure Airflow Connections
```bash
# On Linux/Mac
chmod +x setup_airflow_connections.sh
./setup_airflow_connections.sh

# On Windows PowerShell
.\setup_airflow_connections.ps1
```

### 4. Access the Services
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **MySQL**: localhost:3306 (airflow/airflow)

### 5. Verify Spark Cluster
```bash
# Test your distributed Spark cluster
python verify_spark_cluster.py
```

### 6. Monitor Services
- **Spark Master UI**: http://localhost:8088
- **Spark Worker 1 UI**: http://localhost:8081
- **Spark Worker 2 UI**: http://localhost:8082

### 7. Run the Pipeline
1. Open Airflow UI (http://localhost:8080)
2. Find the `nasa_neo_pipeline` DAG
3. Enable the DAG (toggle switch)
4. Trigger manually or wait for scheduled execution

## 🐍 Python Version Consistency Fix

**Issue Resolved**: Fixed Python version mismatch between Airflow (Python 3.12) and Spark workers (Python 3.8)

**Solution**: All containers now use **Python 3.10.8** consistently:
- **Airflow containers**: Python 3.10.8 (via `apache/airflow:2.10.4-python3.10`)
- **Spark cluster**: Python 3.10.8 (via `apache/spark:3.5.7-java17` with environment variables)
- **PySpark version**: 3.5.7 (matching Spark cluster version)

**Environment Variables Added**:
```yaml
PYSPARK_PYTHON: python3.10
PYSPARK_DRIVER_PYTHON: python3.10
```

## 📁 Project Structure

```
airflow_innovx/
├── dags/
│   └── nasa_neo_pipeline.py      # Main Airflow DAG
├── config/
│   └── airflow.cfg               # Airflow configuration
├── requirements.txt              # Python dependencies
├── docker-compose.yaml          # Docker services
├── DATA_PROCESSING.ipynb         # Development notebook
├── setup_airflow_connections.*   # Setup scripts
└── README.md                     # This file
```

## 🎛️ Configuration

### Environment Variables
Create a `.env` file or set these in your environment:

```env
# NASA API Configuration
NASA_API_KEY=your_nasa_api_key_here

# MySQL Configuration
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=airflow
MYSQL_PASSWORD=airflow
MYSQL_DATABASE=airflow
```

### Airflow DAG Configuration
The pipeline runs **every 7 days** by default. To modify:

```python
# In dags/nasa_neo_pipeline.py
schedule_interval=timedelta(days=7)  # Change this value
```

## 📊 Data Schema

The processed data is stored in the `nasa_neo_data` table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(20) | Unique NEO identifier |
| `neo_reference_id` | VARCHAR(20) | NASA reference ID |
| `name` | VARCHAR(255) | Object name |
| `absolute_magnitude_h` | DECIMAL(10,6) | Absolute magnitude |
| `is_potentially_hazardous_asteroid` | BOOLEAN | Hazard classification |
| `estimated_diameter_km_max` | DECIMAL(15,6) | Max diameter (km) |
| `estimated_diameter_km_min` | DECIMAL(15,6) | Min diameter (km) |
| `close_approach_date_full` | VARCHAR(50) | Approach timestamp |
| `velocity_kps` | DECIMAL(15,6) | Velocity (km/s) |
| `miss_distance_km` | DECIMAL(20,6) | Miss distance (km) |
| `orbiting_body` | VARCHAR(50) | Target body |
| `observation_date` | DATE | Data observation date |
| `is_sentry_object` | BOOLEAN | Sentry monitoring status |

## 🔍 Monitoring & Troubleshooting

### Check DAG Status
```bash
# View DAG runs
docker-compose exec airflow-webserver airflow dags list

# Check specific DAG
docker-compose exec airflow-webserver airflow dags show nasa_neo_pipeline
```

### View Logs
```bash
# Airflow logs
docker-compose logs airflow-scheduler
docker-compose logs airflow-webserver

# MySQL logs
docker-compose logs mysql

# Spark logs (if using external Spark)
docker-compose logs spark-master
```

### Database Queries
```sql
-- Check data quality
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT observation_date) as unique_dates,
    SUM(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 ELSE 0 END) as hazardous_count
FROM nasa_neo_data;

-- View recent data
SELECT * FROM nasa_neo_data 
ORDER BY created_at DESC 
LIMIT 10;
```

## 🛡️ Security Best Practices

1. **API Key Management**: Store NASA API key in Airflow Variables or environment variables
2. **Database Security**: Use strong passwords and limit access
3. **Network Security**: Configure Docker network properly
4. **Data Validation**: Implement data quality checks

## 📈 Performance Optimization

### Spark Configuration
```python
# Adjust based on your system resources
.config("spark.executor.memory", "4g")
.config("spark.driver.memory", "2g")
.config("spark.executor.cores", "4")
```

### MySQL Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX idx_observation_date ON nasa_neo_data(observation_date);
CREATE INDEX idx_hazardous ON nasa_neo_data(is_potentially_hazardous_asteroid);
```

## 🔄 Backup & Recovery

### Data Backup
```bash
# Backup MySQL data
docker-compose exec mysql mysqldump -u airflow -p airflow nasa_neo_data > backup.sql

# Backup Airflow metadata
docker-compose exec mysql mysqldump -u airflow -p airflow > airflow_backup.sql
```

### Data Recovery
```bash
# Restore from backup
docker-compose exec -i mysql mysql -u airflow -p airflow < backup.sql
```

## 📝 Development

### Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Run the Jupyter notebook: `jupyter notebook DATA_PROCESSING.ipynb`
3. Test individual components before deploying to Airflow

### Adding New Features
1. Modify the DAG in `dags/nasa_neo_pipeline.py`
2. Test in the development notebook
3. Update documentation and requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Airflow logs
3. Consult the NASA API documentation
4. Open an issue in the repository

## 🎉 Acknowledgments

- NASA for providing the NEO API
- Apache Airflow, Spark, and MySQL communities
- Docker for containerization platform