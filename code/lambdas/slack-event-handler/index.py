import json
import os
import boto3
import urllib3

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
    
    # Invoke the Bedrock agent
    client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))
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
    slack_token = os.getenv("SLACK_BOT_TOKEN")
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
