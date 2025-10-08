from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator



def greet_user(ti, age):
    first_name=ti.xcom_pull(task_ids='hello_user', key='First_name')
    last_name=ti.xcom_pull(task_ids='hello_user', key='Last_name')
    print(f"Greetings, {first_name} ,{last_name}! You are {age} years old.")

def hello_user(ti):
    first_name=ti.xcom_push(key='First_name', value='Mouad')
    last_name=ti.xcom_push(key='Last_name', value='Moulay')
    


with DAG(
    dag_id='dag2.v2.0',
    start_date=datetime(2025, 7, 1),  # Date de début du DAG
    schedule_interval='0 3 * * Tue',  # Exécute le DAG tous les mardis à 03:00
    catchup=False,

    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    }

) as dag:

    task_3 = PythonOperator(
        task_id='hello_user',
        python_callable=hello_user,
    )

    task_4 = PythonOperator(
        task_id='greet_user',
        python_callable=greet_user,
        op_kwargs={'age': 5},
    )
    task_3 >> task_4  # Set task dependencies

