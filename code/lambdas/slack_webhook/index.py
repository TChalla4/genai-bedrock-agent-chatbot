import json
import os
import boto3
import time
import logging
import hashlib
import hmac
import re
from botocore.exceptions import ClientError

# AWS Clients
bedrock_agent = boto3.client('bedrock-agent-runtime')
secretsmanager = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment Variables
SLACK_SECRET_ARN = os.environ['SLACK_SECRET_ARN']
BEDROCK_AGENT_ID = os.environ['BEDROCK_AGENT_ID']
SESSION_TABLE_NAME = os.environ['SESSION_TABLE_NAME']

# DynamoDB Table
session_table = dynamodb.Table(SESSION_TABLE_NAME)

# Session Expiration (24 hours)
SESSION_TTL = 86400

def get_slack_token():
    """Retrieve Slack token and signing secret."""
    try:
        response = secretsmanager.get_secret_value(SecretId=SLACK_SECRET_ARN)
        secret = json.loads(response['SecretString'])
        return secret['slack_token'], secret['slack_signing_secret']
    except ClientError as e:
        logger.error(f"Error retrieving Slack secret: {e}")
        raise

def verify_slack_request(event, signing_secret):
    """Verify Slack request authenticity."""
    try:
        slack_signature = event['headers'].get('X-Slack-Signature', '')
        slack_timestamp = event['headers'].get('X-Slack-Request-Timestamp', '')

        if not slack_signature or not slack_timestamp:
            return False

        if abs(int(time.time()) - int(slack_timestamp)) > 300:
            return False  # Prevent replay attacks

        base_string = f"v0:{slack_timestamp}:{event['body']}"
        my_signature = 'v0=' + hmac.new(
            bytes(signing_secret, 'utf-8'),
            bytes(base_string, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, slack_signature)
    except Exception as e:
        logger.error(f"Error verifying Slack request: {e}")
        return False

def get_or_create_session(thread_id):
    """Retrieve or create a session in DynamoDB."""
    try:
        response = session_table.get_item(Key={'slack_thread_id': thread_id})

        if 'Item' in response:
            return response['Item']['bedrock_session_id']

        session_id = f"session-{thread_id}-{int(time.time())}"
        session_table.put_item(
            Item={
                'slack_thread_id': thread_id,
                'bedrock_session_id': session_id,
                'ttl': int(time.time()) + SESSION_TTL
            }
        )
        return session_id
    except Exception as e:
        logger.error(f"Error managing session: {e}")
        return f"fallback-{thread_id}"

def invoke_bedrock_agent(text, session_id):
    """Send message to Bedrock and get response."""
    try:
        response = bedrock_agent.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            sessionId=session_id,
            inputText=text
        )
        return response.get('completion', 'I’m not sure how to respond.')
    except Exception as e:
        logger.error(f"Error invoking Bedrock agent: {e}")
        return "I'm having trouble understanding right now."

def post_message_to_slack(token, channel, thread_ts, text):
    """Post a message to Slack."""
    import requests  # Import here to keep Lambda runtime lightweight
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "channel": channel,
            "thread_ts": thread_ts,
            "text": text
        }
    )
    return response.json()

def lambda_handler(event, context):
    """Lambda function to process Slack messages."""
    try:
        slack_token, signing_secret = get_slack_token()

        if not verify_slack_request(event, signing_secret):
            return {'statusCode': 403, 'body': json.dumps('Invalid request')}

        body = json.loads(event['body'])

        # Slack Challenge Verification
        if body.get('type') == 'url_verification':
            return {'statusCode': 200, 'body': json.dumps({'challenge': body['challenge']})}

        message_event = body.get('event', {})
        if message_event.get('type') != 'message':
            return {'statusCode': 200, 'body': json.dumps('Ignored event')}

        channel_id = message_event.get('channel')
        text = message_event.get('text', '').strip()
        thread_ts = message_event.get('thread_ts', message_event.get('ts'))

        # Check if the bot was mentioned
        bot_user_id = "<@U12345678>"  # Replace with your bot's actual Slack ID
        if bot_user_id not in text:
            return {'statusCode': 200, 'body': json.dumps('Bot was not mentioned, ignoring')}

        # Remove bot mention from text
        clean_text = re.sub(f"{bot_user_id}\\s*", "", text).strip()

        # Get session ID
        session_id = get_or_create_session(thread_ts)

        # Get response from Bedrock
        agent_response = invoke_bedrock_agent(clean_text, session_id)

        # Respond to Slack
        post_message_to_slack(slack_token, channel_id, thread_ts, agent_response)

        return {'statusCode': 200, 'body': json.dumps('Message processed')}

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {'statusCode': 500, 'body': json.dumps('Internal server error')}
