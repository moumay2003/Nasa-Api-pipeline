#!/usr/bin/env python3
"""
Configure Spark connection in Airflow with proper master URL
"""

import os
import sys
sys.path.append('/opt/airflow')

from airflow.models import Connection
from airflow import settings
from airflow.utils.db import provide_session

def setup_spark_connection():
    """Setup Spark connection with correct master URL"""
    session = settings.Session()
    
    try:
        # Delete existing connection if it exists
        existing_conn = session.query(Connection).filter(Connection.conn_id == 'spark_default').first()
        if existing_conn:
            session.delete(existing_conn)
            session.commit()
            print("Deleted existing spark_default connection")
        
        # Create new Spark connection with proper configuration
        spark_conn = Connection(
            conn_id='spark_default',
            conn_type='spark',
            host='spark-master',
            port=7077,
            extra='{"master": "spark://spark-master:7077"}'
        )
        
        session.add(spark_conn)
        session.commit()
        
        print("✅ Spark connection created successfully!")
        print(f"   • Connection ID: {spark_conn.conn_id}")
        print(f"   • Host: {spark_conn.host}")
        print(f"   • Port: {spark_conn.port}")
        print(f"   • Extra: {spark_conn.extra}")
        print(f"   • URI: {spark_conn.get_uri()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create Spark connection: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    if setup_spark_connection():
        print("\n🎉 Spark connection setup completed!")
    else:
        print("\n❌ Spark connection setup failed!")
        sys.exit(1)