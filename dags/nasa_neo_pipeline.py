"""
NASA Near-Earth Objects (NEO) Data Pipeline
Automated data extraction, processing, and MySQL storage every 7 days
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
import logging
import os
import sys

# PySpark processing is handled by SparkSubmitOperator using spark_neo_processor.py

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

# Removed get_spark_session function - using SparkSubmitOperator instead

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
        
        # Save raw data to shared volume for Spark processing
        shared_file = f"/opt/airflow/spark-data/nasa_neo_raw_{context['ds']}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(shared_file), exist_ok=True)
        
        with open(shared_file, 'w') as f:
            json.dump(neo_list, f, indent=2)
        
        logging.info(f"Raw data saved to: {shared_file}")
        
        # Push filename to XCom for next task
        return shared_file
        
    except requests.RequestException as e:
        logging.error(f"❌ API request failed: {e}")
        raise
    except Exception as e:
        logging.error(f"❌ Data extraction failed: {e}")
        raise

# Removed process_neo_data function - using SparkSubmitOperator with spark_neo_processor.py script

def load_to_mysql(**context):
    """
    Load processed NEO data to MySQL database
    """
    try:
        # Get processed data file from shared volume (Spark output)
        processed_file = f"/opt/airflow/spark-data/nasa_neo_processed_{context['ds']}.csv"
        
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
        miss_distance_km DECIMAL(15,6),
        orbiting_body VARCHAR(50),
        date VARCHAR(20),
        is_sentry_object BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        batch_date VARCHAR(20),
        INDEX idx_date (date),
        INDEX idx_batch_date (batch_date),
        INDEX idx_hazardous (is_potentially_hazardous_asteroid)
    );
    """,
    dag=dag,
)

extract_task = PythonOperator(
    task_id='extract_nasa_data',
    python_callable=extract_nasa_neo_data,
    dag=dag,
)

# Use BashOperator to directly call spark-submit with improved client mode configuration
process_task = BashOperator(
    task_id='process_neo_data',
    bash_command="""
    # Get the container's IP address for driver host
    DRIVER_HOST=$(hostname -i)
    echo "Driver host: $DRIVER_HOST"
    
    /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --conf spark.executor.memory=1400m \
        --conf spark.executor.cores=1 \
        --conf spark.driver.memory=1g \
        --conf spark.dynamicAllocation.enabled=false \
        --conf spark.pyspark.python=python3.10 \
        --conf spark.pyspark.driver.python=python3.10 \
        --conf spark.driver.host=$DRIVER_HOST \
        --conf spark.driver.bindAddress=0.0.0.0 \
        --conf spark.network.timeout=600s \
        --conf spark.executor.heartbeatInterval=60s \
        --conf spark.sql.adaptive.enabled=true \
        --conf spark.sql.adaptive.coalescePartitions.enabled=true \
        --name nasa_neo_processing \
        /opt/airflow/spark-data/spark_neo_processor.py \
        {{ ds }}
    """,
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