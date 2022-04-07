import os
import json
import urllib.parse
import zipfile
import boto3
import io
import requests
import json
from base64 import b64decode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import yaml

# Envrionment variables
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
KEYWORD_DEV_LB_DNS_NAME = os.environ['KEYWORD_DEV_LB_DNS_NAME']
AWS_REGION = os.environ['AWS_REGION']
CLIENT_FILE_NAME = os.environ['CLIENT_FILE_NAME']

# boto3 objects
s3 = boto3.resource('s3', AWS_REGION)
code_pipeline = boto3.client('codepipeline', AWS_REGION)

def lambda_handler(event, context):
    try:
        # logging event
        print(event)
        
        # Get meta data of artifacts
        bucket_name = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['bucketName']
        object_key = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['objectKey']
        job_id = event['CodePipeline.job']['id']
        
        # Get client.yml file by decompressing zip file
        client_conf = get_client_conf(bucket_name, object_key, CLIENT_FILE_NAME)

        # Requests to Dev Service
        normal_res = dict()
        abnormal_res = dict()
        for client_name, info in client_conf['service_keys'].items():
            service_key = info[0]
            keyword = info[-1]   
            data = {"service_key": service_key, "keyword": keyword, "type": 1, "topn": 2}
            res = requests.post(url=KEYWORD_DEV_LB_DNS_NAME, data=json.dumps(data))
            if res.status_code == 200:
                print(f"Normal Status: {service_key}", data, res)
                normal_res[service_key] =  f'⭐ {client_name} 🔍 {keyword}  👉 {eval(res.text)["recommendation"]}'
            else:
                print(f"Abnormal Status: {service_key}", data, res)
                abnormal_res[service_key] = f'⭐️   {client_name} 🙁 status code 👉 {res.status_code}'
    
        # Send Slack Messages
        send_slack_message(SLACK_CHANNEL, SLACK_WEBHOOK_URL, "😀 SUCCESS\n" + str(json.dumps(normal_res, indent=6, ensure_ascii=False)))
        send_slack_message(SLACK_CHANNEL, SLACK_WEBHOOK_URL, "💩 ERROR\n" + str(json.dumps(abnormal_res, indent=6, ensure_ascii=False)))
        put_job_success(job_id, "Success")

    except Exception as e:
        print("Function failed due to exception.")
        print(e)
        put_job_failure(job_id, 'Function exception: ' + str(e))
        

def send_slack_message(slack_channel, slack_webhook_url, text):
    slack_message = {
        "channel": slack_channel,
        "text": text
    }
    req = Request(slack_webhook_url, json.dumps(slack_message).encode('utf-8'))
    response = urlopen(req)
    response.read()
    
def put_job_success(job_id, message):
    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job_id)
  
def put_job_failure(job_id, message):
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job_id, failureDetails={'message': message, 'type': 'JobFailed'})
    
def get_client_conf(bucket_name, object_key, client_file_name):
    obj = s3.Object(bucket_name=bucket_name, key=object_key)
    buffer = io.BytesIO(obj.get()["Body"].read())
    with zipfile.ZipFile(buffer) as zipf:
        for file in zipf.infolist():
            if file.filename == client_file_name:
                tmp = zipf.open(file).read()
                client_conf = yaml.safe_load(tmp)
    return client_conf
    
    