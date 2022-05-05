# functions
def get_client_names(**context):
    with open("/data/airflow/G2R12N-DAGS/clients.yml", "r", encoding="utf-8") as f:
        clients = yaml.safe_load(f)

    client_list = []
    for k, v in clients.items():
        if clients[k]["keyword"]["use"] == "Y":
            client_list.append(clients[k]["name"])

    return client_list


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
        # wait until task of DAG is completed
        external_task_id=None, 
        execution_date_fn=lambda dt: get_parent_dag_execution_date(client_name),
        mode="reschedule",
        # fail after 10Hrs
        timeout=7200,  
        queue="main",
        dag=dag,
    )

    return parent_task_sensor


# dag
dag_name = "keyword_dag_dependency"

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
