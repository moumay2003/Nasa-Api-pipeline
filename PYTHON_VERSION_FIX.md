# Python Version Troubleshooting Guide

## 🐍 Python Version Consistency Issues - SOLVED! ✅

### Problem Description
Previously, the NASA NEO pipeline suffered from Python version inconsistencies:
- **Airflow containers**: Python 3.12 (driver)
- **Spark workers**: Python 3.8 (executors)
- **Result**: Serialization errors, failed tasks, and connection issues

### Solution Implemented ✅

#### 1. Updated Docker Images
- **Airflow**: `apache/airflow:2.10.4-python3.10` (was `apache/airflow:2.10.4`)
- **Spark**: `apache/spark:3.5.7-java17` (was `apache/spark:3.4.1`)
- **PySpark**: `3.5.7` (was `3.4.1`)

#### 2. Environment Variables Added
```yaml
# In docker-compose.yaml for all services
PYSPARK_PYTHON: python3.10
PYSPARK_DRIVER_PYTHON: python3.10
```

#### 3. Spark Configuration Updated
```python
# In nasa_neo_pipeline.py and verify_spark_cluster.py
os.environ['PYSPARK_PYTHON'] = 'python3.10'
os.environ['PYSPARK_DRIVER_PYTHON'] = 'python3.10'

# Additional Spark configs
.config("spark.pyspark.python", "python3.10")
.config("spark.pyspark.driver.python", "python3.10")
```

## 🔧 Quick Fix Commands

### Method 1: Automated Update (Recommended)
```powershell
# Run the automated update script
.\update_environment.ps1
```

### Method 2: Manual Update
```powershell
# Stop current containers
docker-compose down

# Remove old images
docker image rm extending_airflow:latest
docker image rm apache/spark:3.4.1

# Pull new Spark image
docker pull apache/spark:3.5.7-java17

# Rebuild with new configuration
docker-compose build --no-cache

# Start updated environment
docker-compose up -d
```

## 🔍 Validation Commands

### Check Python Versions
```powershell
# Automated validation
python validate_python_versions.py

# Manual checks
docker-compose exec airflow-webserver python --version
docker-compose exec spark-master python3 --version
docker-compose exec spark-worker python3 --version
```

### Test Spark Connectivity
```powershell
# Verify distributed Spark cluster
python verify_spark_cluster.py
```

## 🚨 Common Error Messages (Now Fixed!)

### Before Fix ❌
```
py4j.protocol.Py4JException: Method isBarrier([class java.lang.Boolean]) does not exist
TypeError: 'JavaPackage' object is not callable
pyspark.serializers.DeserializationError: Could not deserialize object
```

### After Fix ✅
```
✅ Spark session created successfully!
✅ Cluster Test Result: 10 ✅
✅ All containers use consistent Python versions!
```

## 📊 Version Matrix

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| Airflow | Python 3.12 | Python 3.10.8 | ✅ Fixed |
| Spark Master | Python 3.8 | Python 3.10.8 | ✅ Fixed |
| Spark Workers | Python 3.8 | Python 3.10.8 | ✅ Fixed |
| PySpark | 3.4.1 | 3.5.7 | ✅ Updated |
| Java | JDK 11 | JDK 17 | ✅ Updated |

## 🎯 Verification Checklist

- [ ] All containers start successfully
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] Spark Master UI shows 2 active workers at http://localhost:8088
- [ ] Python version validation passes
- [ ] Spark cluster verification succeeds
- [ ] NASA NEO pipeline DAG runs without errors

## 🔮 Future Maintenance

### When Updating Images
1. Always check Python version compatibility
2. Update both Airflow and Spark images together
3. Test with validation scripts before production
4. Document any version changes

### Best Practices
- Pin specific Python versions in Docker images
- Use environment variables for consistency
- Test Spark connectivity after updates
- Monitor logs for version-related warnings

## 📞 Need Help?

If you still encounter Python version issues:
1. Run `python validate_python_versions.py`
2. Check container logs: `docker-compose logs [service-name]`
3. Verify environment variables are set correctly
4. Ensure all containers are using the updated images

Remember: Consistency is key! All Python environments must match for distributed computing to work properly.