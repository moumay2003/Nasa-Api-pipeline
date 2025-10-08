from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator



def ptint_import():
    import matplotlib
    print(f"Matplotlib version: {matplotlib.__version__}")

with DAG(
    dag_id='dag_verify',
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

 

    task_3 = PythonOperator(
        task_id='task_3',
        python_callable=ptint_import,
    )

    task_3  # Set task dependencies
