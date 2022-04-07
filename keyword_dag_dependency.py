from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.models import DagRun
from airflow.operators.sensors import ExternalTaskSensor
from airflow.contrib.hooks.slack_webhook_hook import SlackWebhookHook
from datetime import timedelta, datetime
import yaml

# functions
def get_client_names(**context):
    with open("/data/airflow/G2R12N-DAGS/clients.yml", "r", encoding="utf-8") as f:
        clients = yaml.safe_load(f)

    client_list = []
    for k, v in clients.items():
        if clients[k]["keyword"]["use"] == "Y":
            client_list.append(clients[k]["name"])

    return client_list


def slack_fail_alert(context):
    alert = SlackWebhookHook(
        http_conn_id="slack",
        channel="#datascience",
        username="airflow_bot",
        message="""
                :red_circle: Task Failed. 
                *Task*: {task}  
                *Dag*: {dag} 
                *Execution Time*: {exec_date}  
                # modify base_url param of airflow.cfg
                """.format(
            task=context.get("task_instance").task_id,
            dag=context.get("task_instance").dag_id,
            ti=context.get("task_instance"),
            exec_date=context.get("execution_date"),
            log_url=context.get("task_instance").log_url,
        ),
    )
    return alert.execute()


def slack_success_alert(context):
    alert = SlackWebhookHook(
        http_conn_id="slack",
        channel="#datascience",
        username="airflow_bot",
        message="""
                :green_heart: Task Successed. 
                *Task*: {task}  
                *Dag*: {dag} 
                *Execution Time*: {exec_date}  
                # modify base_url param of airflow.cfg
                """.format(
            task=context.get("task_instance").task_id,
            dag=context.get("task_instance").dag_id,
            ti=context.get("task_instance"),
            exec_date=context.get("execution_date"),
            log_url=context.get("task_instance").log_url,
        ),
    )
    return alert.execute()


def get_parent_dag_execution_date(client_name):
    # find latest scheduled or manual dag run
    dag_runs = DagRun.find(dag_id="keyword_{}_v2.0".format(client_name))
    dag_run = dag_runs[-1]
    external_dag_run_execution_date = dag_run.execution_date
    return external_dag_run_execution_date


def create_parent_task_sensor(client_name):
    parent_task_sensor = ExternalTaskSensor(
        task_id="keyword_{}_sensor".format(client_name),
        external_dag_id="keyword_{}_v2.0".format(client_name),
        external_task_id=None,  # wait until task of DAG is completed
        execution_date_fn=lambda dt: get_parent_dag_execution_date(client_name),
        mode="reschedule",
        timeout=7200,  # fail after 10Hrs
        queue="main",
        dag=dag,
    )

    return parent_task_sensor


# dag
dag_name = "keyword_dag_dependency"

default_args = {
    "owner": "airflow",  # owner name of the DAG
    "depends_on_past": False,  # whether to rely on previous task status
    "start_date": datetime(2021, 4, 30),  # start date of task instance
    # "on_success_callback": slack_success_alert,
    "on_failure_callback": slack_fail_alert,
    "retries": 1,  # retry the task once, if it fails
    "retry_delay": timedelta(minutes=3),  # after waiting for 3 min
}

with DAG(dag_name, default_args=default_args, schedule_interval="0 6 * * 1-5") as dag:

    trigger_keyword_train_dag = BashOperator(
        task_id="trigger_keyword_train_dag",
        bash_command="airflow trigger_dag keyword_train",
        queue="keyword_train",
        dag=dag,
    )

    client_list = get_client_names()
    for client_name in client_list:
        client_sensor = create_parent_task_sensor(client_name)
        client_sensor >> trigger_keyword_train_dag
