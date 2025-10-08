from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
def print_hello(name , age):
    print(f"Hello, {name} You are {age} years old.")

with DAG(
    dag_id='mon_premier_dag',
    start_date=datetime(2025, 7, 1),  # Date de début du DAG
    schedule_interval='@daily',
    catchup=False,

    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    }

) as dag:
    task_1 = BashOperator(  
        task_id='task_1',
        bash_command='echo "Hello, Airflow!"',
    )

    task_2 = BashOperator(
        task_id='task_2',
        bash_command='echo "This is my first DAG!"',

    )

    task_1 >> task_2  # Set task dependencies


    task_3 = PythonOperator(
        task_id='task_3',
        python_callable=print_hello,
        op_kwargs={'name': 'Airflow', 'age': 5},
    )




    













