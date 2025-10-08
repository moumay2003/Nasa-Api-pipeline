#!/usr/bin/env python3
"""
Test Spark Cluster Connection
Run this script to verify connectivity between Airflow and Spark cluster
"""

import os
import sys
import socket
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_network_connectivity():
    """Test basic network connectivity to Spark master"""
    print("🌐 NETWORK CONNECTIVITY TEST")
    print("=" * 50)
    
    spark_host = "spark-master"
    spark_port = 7077
    
    try:
        # Test DNS resolution
        ip_address = socket.gethostbyname(spark_host)
        print(f"✅ DNS Resolution: {spark_host} -> {ip_address}")
        
        # Test socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((spark_host, spark_port))
        sock.close()
        
        if result == 0:
            print(f"✅ Socket Connection: {spark_host}:{spark_port} is accessible")
            return True
        else:
            print(f"❌ Socket Connection: {spark_host}:{spark_port} is not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def test_spark_installation():
    """Test if Spark is properly installed"""
    print("\n🔧 SPARK INSTALLATION TEST")
    print("=" * 50)
    
    spark_home = os.getenv('SPARK_HOME', '/opt/spark')
    print(f"SPARK_HOME: {spark_home}")
    
    # Check if SPARK_HOME exists
    if not os.path.exists(spark_home):
        print(f"❌ SPARK_HOME directory not found: {spark_home}")
        return False
    
    # Check for key Spark files
    spark_submit = os.path.join(spark_home, 'bin', 'spark-submit')
    pyspark_py = os.path.join(spark_home, 'python', 'pyspark')
    
    if os.path.exists(spark_submit):
        print(f"✅ Found spark-submit: {spark_submit}")
    else:
        print(f"❌ Missing spark-submit: {spark_submit}")
        return False
        
    if os.path.exists(pyspark_py):
        print(f"✅ Found PySpark: {pyspark_py}")
    else:
        print(f"❌ Missing PySpark: {pyspark_py}")
        return False
    
    # Test Spark version
    try:
        result = subprocess.run([spark_submit, '--version'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            version_line = [line for line in result.stderr.split('\n') if 'version' in line.lower()]
            if version_line:
                print(f"✅ Spark Version: {version_line[0].strip()}")
            else:
                print("✅ Spark is executable")
        else:
            print(f"❌ Spark version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Spark version test failed: {e}")
        return False
    
    return True

def test_pyspark_connection():
    """Test PySpark connection to cluster"""
    print("\n⚡ PYSPARK CONNECTION TEST")
    print("=" * 50)
    
    try:
        # Set environment variables
        spark_home = os.getenv('SPARK_HOME', '/opt/spark')
        os.environ['PYTHONPATH'] = f"{spark_home}/python:{spark_home}/python/lib/py4j-0.10.9.7-src.zip:{os.environ.get('PYTHONPATH', '')}"
        os.environ['PYSPARK_PYTHON'] = 'python3.10'
        os.environ['PYSPARK_DRIVER_PYTHON'] = 'python3.10'
        
        from pyspark.sql import SparkSession
        
        # Try to create SparkSession with cluster
        spark_master = "spark://spark-master:7077"
        print(f"Attempting connection to: {spark_master}")
        
        spark = SparkSession.builder \
            .appName("connectivity_test") \
            .master(spark_master) \
            .config("spark.executor.memory", "1g") \
            .config("spark.executor.cores", "1") \
            .config("spark.driver.memory", "512m") \
            .config("spark.driver.host", "0.0.0.0") \
            .config("spark.driver.bindAddress", "0.0.0.0") \
            .config("spark.network.timeout", "60s") \
            .config("spark.pyspark.python", "python3.10") \
            .config("spark.pyspark.driver.python", "python3.10") \
            .getOrCreate()
        
        # Test basic operations
        test_data = [(1, "test"), (2, "spark"), (3, "cluster")]
        df = spark.createDataFrame(test_data, ["id", "value"])
        count = df.count()
        
        print(f"✅ SparkSession created successfully!")
        print(f"   • Application ID: {spark.sparkContext.applicationId}")
        print(f"   • Master URL: {spark.sparkContext.master}")
        print(f"   • Default Parallelism: {spark.sparkContext.defaultParallelism}")
        print(f"   • Test DataFrame count: {count}")
        
        # Clean up
        spark.stop()
        return True
        
    except Exception as e:
        print(f"❌ PySpark connection failed: {e}")
        return False

def main():
    """Run all connectivity tests"""
    print("🚀 SPARK CLUSTER CONNECTIVITY TEST")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Container: {socket.gethostname()}")
    print("=" * 60)
    
    tests = [
        ("Network Connectivity", test_network_connectivity),
        ("Spark Installation", test_spark_installation),
        ("PySpark Connection", test_pyspark_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Spark cluster is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())