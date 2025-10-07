"""
NASA Near-Earth Objects (NEO) Data Pipeline
Automated data extraction, processing, and MySQL storage every 7 days
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import logging
import os
import sys

# Add PySpark imports
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract
from pyspark.sql.types import *

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

# DAG definition
dag = DAG(
    'nasa_neo_pipeline',
    default_args=default_args,
    description='NASA NEO data extraction, processing, and MySQL storage',
    schedule_interval=timedelta(days=7),  # Run every 7 days
    start_date=datetime(2025, 10, 5),
    catchup=False,
    max_active_runs=1,
    tags=['nasa', 'neo', 'etl', 'spark', 'mysql'],
)

def get_spark_session():
    """Initialize Spark session with distributed cluster configuration"""
    # Set Python executables for distributed Spark cluster
    os.environ['PYSPARK_PYTHON'] = 'python3'
    os.environ['PYSPARK_DRIVER_PYTHON'] = 'python3'
    
    # Get Spark master URL from environment or use default
    spark_master = os.getenv('SPARK_MASTER_URL', 'spark://spark-master:7077')
    
    # Get the current container's hostname/IP for driver
    import socket
    driver_host = socket.gethostname()
    
    logging.info(f"🔧 Connecting to Spark cluster at: {spark_master}")
    logging.info(f"🖥️ Driver host: {driver_host}")
    
    spark = SparkSession.builder \
        .appName("nasa_neo_etl_distributed") \
        .master(spark_master) \
        .config("spark.executor.memory", "1800m") \
        .config("spark.executor.cores", "2") \
        .config("spark.cores.max", "4") \
        .config("spark.driver.memory", "1g") \
        .config("spark.driver.maxResultSize", "1g") \
        .config("spark.driver.host", driver_host) \
        .config("spark.driver.port", "0") \
        .config("spark.driver.bindAddress", "0.0.0.0") \
        .config("spark.blockManager.port", "0") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .config("spark.network.timeout", "600s") \
        .config("spark.executor.heartbeatInterval", "60s") \
        .config("spark.dynamicAllocation.enabled", "false") \
        .config("spark.submit.deployMode", "client") \
        .config("spark.ui.port", "4040") \
        .getOrCreate()
    
    # Verify cluster connection
    try:
        spark_context = spark.sparkContext
        logging.info(f"✅ Spark session created successfully!")
        logging.info(f"   • Spark Version: {spark.version}")
        logging.info(f"   • Master URL: {spark_master}")
        logging.info(f"   • Application ID: {spark_context.applicationId}")
        logging.info(f"   • Default Parallelism: {spark_context.defaultParallelism}")
        logging.info(f"   • Available Executors: {len(spark_context._jsc.sc().statusTracker().getExecutorInfos()) - 1}")
        
        # Test the connection with a simple operation
        test_rdd = spark_context.parallelize([1, 2, 3, 4])
        result = test_rdd.sum()
        logging.info(f"   • Cluster Test Result: {result} ✅")
        
    except Exception as e:
        logging.warning(f"⚠️ Cluster verification failed: {e}")
        logging.info("Continuing with available resources...")
    
    return spark

def extract_nasa_neo_data(**context):
    """
    Extract NASA NEO data from API for the last 7 days
    """
    try:
        # Get API key from environment variables (more secure)
        api_key = os.getenv('NASA_API_KEY', '3NcI1W7rKoehu3KEtqGFjh4nwV6nuO6v7a3WhYrC')
        
        # Calculate date range (last 7 days from execution date)
        execution_date = context['execution_date']
        start_date = (execution_date - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = execution_date.strftime('%Y-%m-%d')
        
        logging.info(f"Extracting NASA NEO data from {start_date} to {end_date}")
        
        # API request
        url = (f"https://api.nasa.gov/neo/rest/v1/feed"
               f"?start_date={start_date}&end_date={end_date}&api_key={api_key}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Validate response
        if 'near_earth_objects' not in data:
            raise ValueError("Invalid API response: missing near_earth_objects")
        
        # Flatten the nested structure
        neo_list = []
        for date, objects in data["near_earth_objects"].items():
            for obj in objects:
                obj["date"] = date
                neo_list.append(obj)
        
        logging.info(f"✅ Extracted {len(neo_list)} NEO records")
        
        # Save raw data to temporary file for next task
        temp_file = f"/tmp/nasa_neo_raw_{context['ds']}.json"
        with open(temp_file, 'w') as f:
            json.dump(neo_list, f, indent=2)
        
        # Push filename to XCom for next task
        return temp_file
        
    except requests.RequestException as e:
        logging.error(f"❌ API request failed: {e}")
        raise
    except Exception as e:
        logging.error(f"❌ Data extraction failed: {e}")
        raise

def process_neo_data(**context):
    """
    Process NASA NEO data using PySpark
    """
    try:
        # Get the raw data file from previous task
        temp_file = context['task_instance'].xcom_pull(task_ids='extract_nasa_data')
        
        if not os.path.exists(temp_file):
            raise FileNotFoundError(f"Raw data file not found: {temp_file}")
        
        # Load raw data
        with open(temp_file, 'r') as f:
            neo_list = json.load(f)
        
        logging.info(f"Processing {len(neo_list)} NEO records with Spark")
        
        # Initialize Spark session
        spark = get_spark_session()
        
        try:
            # Convert to pandas DataFrame first, then to Spark DataFrame
            pandas_df = pd.DataFrame(neo_list)
            df = spark.createDataFrame(pandas_df)
            
            # Process the data - extract nested fields
            df_processed = df.withColumn("estimated_diameter_km_max", 
                                       col("estimated_diameter").getItem("kilometers").getItem("estimated_diameter_max")) \
                            .withColumn("estimated_diameter_km_min", 
                                       col("estimated_diameter").getItem("kilometers").getItem("estimated_diameter_min"))
            
            # Extract close approach data (first approach only)
            df_with_approach = df_processed.withColumn("close_approach_date_full", 
                                                     col("close_approach_data").getItem(0).getItem("close_approach_date_full")) \
                                         .withColumn("velocity_kps_str", 
                                                    col("close_approach_data").getItem(0).getItem("relative_velocity")) \
                                         .withColumn("miss_distance_str", 
                                                    col("close_approach_data").getItem(0).getItem("miss_distance")) \
                                         .withColumn("orbiting_body", 
                                                    col("close_approach_data").getItem(0).getItem("orbiting_body"))
            
            # Extract numerical values from nested string maps using regex
            df_final = df_with_approach.withColumn("velocity_kps", 
                                                 regexp_extract(col("velocity_kps_str"), r"kilometers_per_second=([0-9.]+)", 1).cast("double")) \
                                       .withColumn("miss_distance_km", 
                                                  regexp_extract(col("miss_distance_str"), r"kilometers=([0-9.]+)", 1).cast("double"))
            
            # Select final columns
            df_clean = df_final.select(
                "id",
                "neo_reference_id", 
                "name",
                "absolute_magnitude_h", 
                "is_potentially_hazardous_asteroid", 
                "estimated_diameter_km_max", 
                "estimated_diameter_km_min", 
                "close_approach_date_full", 
                "velocity_kps", 
                "miss_distance_km", 
                "orbiting_body",
                "date",
                "is_sentry_object"
            )
            
            # Convert back to Pandas for easier MySQL insertion
            processed_data = df_clean.toPandas()
            
            logging.info(f"✅ Processed {len(processed_data)} records")
            logging.info(f"Columns: {list(processed_data.columns)}")
            
            # Save processed data
            processed_file = f"/tmp/nasa_neo_processed_{context['ds']}.csv"
            processed_data.to_csv(processed_file, index=False)
            
            return processed_file
            
        finally:
            spark.stop()
            
    except Exception as e:
        logging.error(f"❌ Data processing failed: {e}")
        raise

def load_to_mysql(**context):
    """
    Load processed NEO data to MySQL database
    """
    try:
        # Get processed data file from previous task
        processed_file = context['task_instance'].xcom_pull(task_ids='process_neo_data')
        
        if not os.path.exists(processed_file):
            raise FileNotFoundError(f"Processed data file not found: {processed_file}")
        
        # Load processed data
        df = pd.read_csv(processed_file)
        
        logging.info(f"Loading {len(df)} records to MySQL")
        
        # Get MySQL connection
        mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
        
        # Data quality checks
        df = df.dropna(subset=['id', 'neo_reference_id'])  # Remove records without essential IDs
        
        # Handle missing values
        df['velocity_kps'] = df['velocity_kps'].fillna(0)
        df['miss_distance_km'] = df['miss_distance_km'].fillna(0)
        df['estimated_diameter_km_max'] = df['estimated_diameter_km_max'].fillna(0)
        df['estimated_diameter_km_min'] = df['estimated_diameter_km_min'].fillna(0)
        
        # Convert boolean columns
        df['is_potentially_hazardous_asteroid'] = df['is_potentially_hazardous_asteroid'].astype(bool)
        df['is_sentry_object'] = df['is_sentry_object'].astype(bool)
        
        # Add metadata
        df['created_at'] = datetime.now()
        df['batch_date'] = context['ds']
        
        # Insert data using pandas to_sql method
        engine = mysql_hook.get_sqlalchemy_engine()
        
        # Insert data (replace existing records with same date)
        df.to_sql(
            name='nasa_neo_data',
            con=engine,
            if_exists='append',  # We'll handle duplicates in the table design
            index=False,
            method='multi'
        )
        
        logging.info(f"✅ Successfully loaded {len(df)} records to MySQL")
        
        # Clean up temporary files
        for temp_file in [context['task_instance'].xcom_pull(task_ids='extract_nasa_data'), processed_file]:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Cleaned up temporary file: {temp_file}")
        
    except Exception as e:
        logging.error(f"❌ MySQL loading failed: {e}")
        raise

# Task definitions
create_table_task = MySqlOperator(
    task_id='create_mysql_table',
    mysql_conn_id='mysql_default',
    sql="""
    CREATE TABLE IF NOT EXISTS nasa_neo_data (
        id VARCHAR(20) PRIMARY KEY,
        neo_reference_id VARCHAR(20) NOT NULL,
        name VARCHAR(255),
        absolute_magnitude_h DECIMAL(10,6),
        is_potentially_hazardous_asteroid BOOLEAN,
        estimated_diameter_km_max DECIMAL(15,6),
        estimated_diameter_km_min DECIMAL(15,6),
        close_approach_date_full VARCHAR(50),
        velocity_kps DECIMAL(15,6),
        miss_distance_km DECIMAL(20,6),
        orbiting_body VARCHAR(50),
        date DATE,
        is_sentry_object BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        batch_date DATE,
        INDEX idx_date (date),
        INDEX idx_hazardous (is_potentially_hazardous_asteroid),
        INDEX idx_batch_date (batch_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    dag=dag,
)

extract_task = PythonOperator(
    task_id='extract_nasa_data',
    python_callable=extract_nasa_neo_data,
    dag=dag,
)

process_task = PythonOperator(
    task_id='process_neo_data',
    python_callable=process_neo_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_mysql',
    python_callable=load_to_mysql,
    dag=dag,
)

# Data quality check task
data_quality_task = MySqlOperator(
    task_id='data_quality_check',
    mysql_conn_id='mysql_default',
    sql="""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT date) as unique_dates,
        SUM(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 ELSE 0 END) as hazardous_count,
        AVG(estimated_diameter_km_max) as avg_diameter,
        MAX(created_at) as last_update
    FROM nasa_neo_data 
    WHERE batch_date = '{{ ds }}';
    """,
    dag=dag,
)

# Define task dependencies
create_table_task >> extract_task >> process_task >> load_task >> data_quality_task