#!/usr/bin/env python3
"""
NASA NEO Data Processing Spark Job
This script runs on the Spark cluster to process NASA NEO data
"""

import sys
import json
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract
from pyspark.sql.types import *
import logging
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: spark_neo_processor.py <execution_date>")
        sys.exit(1)
    
    execution_date = sys.argv[1]
    
    # Define file paths in shared volume (accessible from both Airflow and Spark containers)
    input_file = f"/opt/airflow/spark-data/nasa_neo_raw_{execution_date}.json"
    output_file = f"/opt/airflow/spark-data/nasa_neo_processed_{execution_date}.csv"
    
    # Initialize Spark session - connect to cluster if available, fallback to local
    spark = SparkSession.builder \
        .appName("NASA_NEO_Data_Processing") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    
    try:
        print(f"📊 Processing NASA NEO data from: {input_file}")
        
        # Read the JSON data
        with open(input_file, 'r') as f:
            neo_list = json.load(f)
        
        print(f"📈 Processing {len(neo_list)} NEO records")
        
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
        
        # Convert back to Pandas and save
        processed_data = df_clean.toPandas()
        
        # Save to temporary file first, then move to shared volume
        temp_output = f"/tmp/nasa_neo_processed_{execution_date}.csv"
        processed_data.to_csv(temp_output, index=False)
        
        # Copy to shared volume with proper permissions
        import shutil
        shutil.move(temp_output, output_file)
        
        print(f"✅ Successfully processed {len(processed_data)} records")
        print(f"📁 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()