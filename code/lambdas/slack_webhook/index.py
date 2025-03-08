import json
import os
import boto3
import urllib3
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    http = urllib3.PoolManager()
    
    # Extract the request body
    body = json.loads(event.get("body", "{}"))
    
    # Verify request is from Slack
    if "challenge" in body:
        return {
            "statusCode": 200,
            "body": json.dumps({"challenge": body["challenge"]})
        }
    
    # Extract message details
    event_data = body.get("event", {})
    user = event_data.get("user", "")
    text = event_data.get("text", "")
    channel = event_data.get("channel", "")
    
    if not user or not text or not channel:
        return {"statusCode": 400, "body": "Invalid request"}
    
    # Retrieve Slack bot token securely from AWS Secrets Manager
    secret_name = os.getenv("SLACK_SECRET_ARN")
    region_name = os.getenv("AWS_REGION")
    
    secrets_client = boto3.client("secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
        slack_token = json.loads(get_secret_value_response["SecretString"]).get("SLACK_BOT_TOKEN")
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        return {"statusCode": 500, "body": "Internal server error"}
    
    # Invoke the Bedrock agent
    client = boto3.client("bedrock-runtime", region_name=region_name)
    agent_id = os.getenv("BEDROCK_AGENT_ID")
    
    try:
        response = client.invoke_agent(
            agentId=agent_id,
            inputText=text
        )
        agent_response = json.loads(response["outputText"])
    except Exception as e:
        print(f"Error invoking Bedrock agent: {e}")
        agent_response = "I'm having trouble processing your request right now."
    
    # Post response back to Slack
    slack_url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }
    message_payload = {
        "channel": channel,
        "text": agent_response
    }
    http.request("POST", slack_url, body=json.dumps(message_payload), headers=headers)
    
    return {"statusCode": 200, "body": "Message processed successfully"}
