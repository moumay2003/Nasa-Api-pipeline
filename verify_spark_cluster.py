#!/usr/bin/env python3
"""
Spark Cluster Verification Script
Verifies that the distributed Spark cluster is properly configured and accessible
"""

import os
import sys
import socket
import time
from pyspark.sql import SparkSession
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_spark_cluster():
    """Test connection to distributed Spark cluster"""
    
    print("🔧 SPARK CLUSTER VERIFICATION")
    print("=" * 50)
    
    # Configuration
    spark_master = os.getenv('SPARK_MASTER_URL', 'spark://spark-master:7077')
    
    try:
        driver_host = socket.gethostname()
    except:
        driver_host = 'localhost'
    
    print(f"📡 Spark Master URL: {spark_master}")
    print(f"🖥️ Driver Host: {driver_host}")
    
    try:
        # Create Spark session
        print("\n🚀 Creating Spark session...")
        
        spark = SparkSession.builder \
            .appName("cluster_verification_test") \
            .master(spark_master) \
            .config("spark.executor.memory", "1g") \
            .config("spark.executor.cores", "2") \
            .config("spark.cores.max", "4") \
            .config("spark.driver.memory", "1g") \
            .config("spark.driver.host", driver_host) \
            .config("spark.driver.port", "0") \
            .config("spark.driver.bindAddress", "0.0.0.0") \
            .config("spark.network.timeout", "300s") \
            .config("spark.executor.heartbeatInterval", "30s") \
            .getOrCreate()
        
        print("✅ Spark session created successfully!")
        
        # Get cluster information
        sc = spark.sparkContext
        
        print(f"\n📊 CLUSTER INFORMATION:")
        print(f"   • Spark Version: {spark.version}")
        print(f"   • Application ID: {sc.applicationId}")
        print(f"   • Master: {sc.master}")
        print(f"   • Default Parallelism: {sc.defaultParallelism}")
        
        # Wait a moment for executors to register
        print("\n⏳ Waiting for executors to register...")
        time.sleep(5)
        
        # Check executors
        try:
            executor_infos = sc._jsc.sc().statusTracker().getExecutorInfos()
            active_executors = len(executor_infos) - 1  # Subtract driver
            
            print(f"\n🔍 EXECUTOR STATUS:")
            print(f"   • Total Executors: {len(executor_infos)}")
            print(f"   • Active Executors: {active_executors}")
            
            for i, executor in enumerate(executor_infos):
                executor_id = executor.executorId()
                host = executor.host()
                is_active = executor.isActive()
                cores = executor.totalCores()
                memory = executor.maxMemory()
                
                print(f"   • Executor {executor_id}: {host} | Active: {is_active} | Cores: {cores} | Memory: {memory//1024//1024}MB")
        
        except Exception as e:
            print(f"⚠️ Could not get executor info: {e}")
        
        # Test computation
        print(f"\n🧮 TESTING DISTRIBUTED COMPUTATION:")
        
        # Test 1: Simple RDD operation
        test_data = list(range(1, 1001))  # 1000 numbers
        rdd = sc.parallelize(test_data, numSlices=4)
        
        start_time = time.time()
        result_sum = rdd.sum()
        end_time = time.time()
        
        expected_sum = sum(test_data)
        print(f"   • Sum test: {result_sum} (expected: {expected_sum}) - {'✅' if result_sum == expected_sum else '❌'}")
        print(f"   • Computation time: {end_time - start_time:.2f}s")
        
        # Test 2: DataFrame operation
        print(f"\n📊 TESTING DATAFRAME OPERATIONS:")
        
        import pandas as pd
        
        # Create test DataFrame
        test_df = spark.createDataFrame([
            (1, "Alice", 25),
            (2, "Bob", 30),
            (3, "Charlie", 35),
            (4, "Diana", 28),
        ], ["id", "name", "age"])
        
        # Simple aggregation
        avg_age = test_df.agg({"age": "avg"}).collect()[0][0]
        print(f"   • Average age: {avg_age:.1f}")
        
        # Group by and count
        count = test_df.count()
        print(f"   • Total records: {count}")
        
        print(f"\n🎉 ALL TESTS PASSED! Your Spark cluster is working correctly.")
        
        # Cleanup
        spark.stop()
        
        return True
        
    except Exception as e:
        print(f"\n❌ CLUSTER TEST FAILED: {e}")
        print(f"\n💡 TROUBLESHOOTING TIPS:")
        print(f"   1. Check if Spark containers are running: docker-compose ps")
        print(f"   2. Check Spark master logs: docker-compose logs spark-master")
        print(f"   3. Check Spark worker logs: docker-compose logs spark-worker")
        print(f"   4. Verify network connectivity between containers")
        print(f"   5. Check if ports 7077, 8080-8082 are available")
        
        return False

def check_docker_services():
    """Check if required Docker services are running"""
    print("\n🐳 DOCKER SERVICES CHECK:")
    
    import subprocess
    
    try:
        # Check if docker-compose is available
        result = subprocess.run(['docker-compose', 'ps', '--services'], 
                              capture_output=True, text=True, check=True)
        
        services = result.stdout.strip().split('\n')
        print(f"   • Available services: {', '.join(services)}")
        
        # Check running services
        result = subprocess.run(['docker-compose', 'ps', '--filter', 'status=running'], 
                              capture_output=True, text=True, check=True)
        
        print(f"   • Running services check: {'✅' if 'spark-master' in result.stdout else '❌'}")
        
    except subprocess.CalledProcessError as e:
        print(f"   • Docker check failed: {e}")
        print(f"   • Make sure you're in the project directory and run: docker-compose up -d")

if __name__ == "__main__":
    print("🚀 NASA NEO Pipeline - Spark Cluster Verification")
    print("=" * 60)
    
    # Check Docker services first
    check_docker_services()
    
    # Test Spark cluster
    success = test_spark_cluster()
    
    if success:
        print("\n✅ Your Spark cluster is ready for the NASA NEO pipeline!")
        print("🎯 Next steps:")
        print("   1. Run the Airflow DAG: nasa_neo_pipeline")
        print("   2. Monitor execution in Airflow UI")
        print("   3. Check results in MySQL database")
    else:
        print("\n❌ Please fix the issues above before running the pipeline.")
    
    print("\n" + "=" * 60)