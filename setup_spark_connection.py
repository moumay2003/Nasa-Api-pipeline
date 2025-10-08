#!/usr/bin/env python3
"""
Setup Spark connection in Airflow
This script creates the necessary Airflow connections for Spark cluster
"""

from airflow.models import Connection
from airflow import settings
import logging

def setup_spark_connection():
    """Setup Spark connection in Airflow"""
    session = settings.Session()
    
    try:
        # Check if connection already exists
        existing_conn = session.query(Connection).filter(Connection.conn_id == 'spark_cluster').first()
        
        if existing_conn:
            logging.info("Spark connection already exists, updating...")
            session.delete(existing_conn)
        
        # Create new Spark connection
        spark_conn = Connection(
            conn_id='spark_cluster',
            conn_type='spark',
            host='spark-master',
            port=7077,
            extra={
                'spark-home': '/opt/spark',
                'java-home': '/usr/lib/jvm/java-17-openjdk-amd64'
            }
        )
        
        session.add(spark_conn)
        session.commit()
        
        logging.info("✅ Spark connection created successfully!")
        logging.info(f"   • Connection ID: {spark_conn.conn_id}")
        logging.info(f"   • Host: {spark_conn.host}")
        logging.info(f"   • Port: {spark_conn.port}")
        
    except Exception as e:
        logging.error(f"❌ Failed to create Spark connection: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_spark_connection()