from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.hooks.slack_webhook_hook import SlackWebhookHook
from datetime import timedelta, datetime
from pytz import timezone

# functions
def create_current_dag_run_time(**context):
    run_id = context["templates_dict"]["run_id"]
    is_scheduled = run_id.startswith("scheduled__")
    kst = timezone("Asia/seoul")
    if is_scheduled:
        tmp_now = context["next_execution_date"].timestamp()
    else:
        tmp_now = context["execution_date"].timestamp()
    now = datetime.fromtimestamp(tmp_now, kst).strftime("%y%m%d_%H%M")
    return now


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


# dag
dag_name = "keyword_train"
folder_name = "KEYWORD_TRAIN"
env = "prod"

default_args = {
    "owner": "airflow",  # owner name of the DAG
    "depends_on_past": False,  # whether to rely on previous task status
    "start_date": datetime(2021, 4, 30),  # start date of task instance
    # "on_success_callback": slack_success_alert,
    "on_failure_callback": slack_fail_alert,
    "retries": 1,  # retry the task once, if it fails
    "retry_delay": timedelta(minutes=3),  # after waiting for 3 min
}

with DAG(dag_name, default_args=default_args, schedule_interval=None) as dag:
    # Task
    get_current_dag_run_time = PythonOperator(
        task_id="get_current_dag_run_time",
        queue="keyword_train",
        python_callable=create_current_dag_run_time,
        templates_dict={"run_id": "{{ run_id }}"},
        dag=dag,
        provide_context=True,
    )

    current_dag_run_time = "{{ task_instance.xcom_pull('get_current_dag_run_time', key='return_value') }}"

    preprocess = BashOperator(
        task_id="preprocess",
        bash_command="cd /data/{} && python3 preprocess.py --aws-conf=aws --model-conf=model --clients-conf=clients".format(folder_name),
        # slave 설정
        queue="keyword_train",
        dag=dag,
    )

    ft_modeling = BashOperator(
        task_id="ft_modeling",
        bash_command="cd /data/{} && python3 train.py --aws-conf=aws --model-conf=model".format(folder_name),
        queue="keyword_train",
        dag=dag,
    )

    keyedvector_modeling = BashOperator(
        task_id="keyedvector_modeling",
        bash_command="cd /data/{} && python3 keyedvector.py --aws-conf=aws --model-conf=model".format(folder_name),
        queue="keyword_train",
        dag=dag,
    )

    pack_models = BashOperator(
        task_id="pack_models",
        bash_command="cd /data/{} && python3 pack_models.py --dag-run-time={}".format(folder_name, current_dag_run_time),
        queue="keyword_train",
        xcom_push=True,
        dag=dag,
    )

    bento_saved_path = "{{ task_instance.xcom_pull('pack_models', key='return_value') }}"

    upload_to_s3_with_zip = BashOperator(
        task_id="upload_to_s3_with_zip",
        bash_command="cd /data/{} && python3 upload_to_s3_with_zip.py --aws-conf=aws --dag-run-time={} --bento-saved-path={} --env={}".format(
            folder_name, current_dag_run_time, bento_saved_path, env
        ),
        queue="keyword_train",
        dag=dag,
    )

    remove_all = BashOperator(
        task_id="remove_all",
        bash_command="cd /data/{} && source remove_all.sh {}".format(folder_name, bento_saved_path),
        queue="keyword_train",
        dag=dag,
    )

    get_current_dag_run_time >> preprocess >> ft_modeling >> keyedvector_modeling >> pack_models >> upload_to_s3_with_zip >> remove_all
