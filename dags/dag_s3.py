from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

with DAG(
    dag_id='dag_s3',
    start_date=datetime(2025, 7, 1),  # Date de début du DAG
    schedule_interval='@daily',  # Exécute le DAG tous les jours
    catchup=False,

    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    }

) as dag:

    task_1 = S3KeySensor(
        task_id='s3_key_sensor',
        bucket_name='airflow',
        bucket_key='test.csv',
        aws_conn_id='aws_default',
        mode='poke',
        poke_interval=2,  # Vérifie toutes les 30 secondes
    )

    task_2 = BashOperator(
        task_id='bash_task',
        bash_command='echo "S3 Key exists!"',
    )

    task_1 >> task_2  # Set task dependencies
    