import json
import os
import boto3
import time
import logging
from datetime import datetime, timedelta
import hashlib
import hmac
import urllib.parse
import base64
import re
from botocore.exceptions import ClientError

# Initialize clients
bedrock_agent = boto3.client('bedrock-agent-runtime')
secretsmanager = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
SLACK_SECRET_ARN = os.environ['SLACK_SECRET_ARN']
BEDROCK_AGENT_ID = os.environ['BEDROCK_AGENT_ID']
SESSION_TABLE_NAME = os.environ['SESSION_TABLE_NAME']

# Initialize DynamoDB table
session_table = dynamodb.Table(SESSION_TABLE_NAME)

# Session expiration in seconds (24 hours)
SESSION_TTL = 86400

def get_slack_token():
    """Retrieve Slack signing secret from Secrets Manager."""
    try:
        response = secretsmanager.get_secret_value(SecretId=SLACK_SECRET_ARN)
        secret = json.loads(response['SecretString'])
        return secret['slack_token'], secret['slack_signing_secret']
    except ClientError as e:
        logger.error(f"Error retrieving Slack secret: {e}")
        raise

def verify_slack_request(event, signing_secret):
    """Verify that the request is coming from Slack."""
    try:
        slack_signature = event['headers']['X-Slack-Signature']
        slack_request_timestamp = event['headers']['X-Slack-Request-Timestamp']
        
        # Check timestamp to prevent replay attacks
        current_timestamp = int(time.time())
        if abs(current_timestamp - int(slack_request_timestamp)) > 60 * 5:
            return False
        
        # Create the signature base string
        base_string = f"v0:{slack_request_timestamp}:{event['body']}"
        
        # Create the signature
        my_signature = 'v0=' + hmac.new(
            bytes(signing_secret, 'utf-8'),
            bytes(base_string, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(my_signature, slack_signature)
    except Exception as e:
        logger.error(f"Error verifying Slack request: {e}")
        return False

def get_or_create_session(thread_id, channel_id, user_id):
    """Get existing session or create a new one."""
    try:
        # Try to get an existing session
        response = session_table.get_item(
            Key={
                'slack_thread_id': thread_id,
                'channel_id': channel_id
            }
        )
        
        # If session exists, return the session ID
        if 'Item' in response:
            # Update the TTL to extend session life
            session_table.update_item(
                Key={
                    'slack_thread_id': thread_id,
                    'channel_id': channel_id
                },
                UpdateExpression="set ttl = :ttl, last_activity = :activity",
                ExpressionAttributeValues={
                    ':ttl': int(time.time()) + SESSION_TTL,
                    ':activity': datetime.now().isoformat()
                }
            )
            return response['Item']['bedrock_session_id']
        
        # If no session exists, create a new one
        session_id = f"slack-{thread_id}-{int(time.time())}"
        
        # Store the new session
        session_table.put_item(
            Item={
                'slack_thread_id': thread_id,
                'channel_id': channel_id,
                'user_id': user_id,
                'bedrock_session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'ttl': int(time.time()) + SESSION_TTL
            }
        )
        
        return session_id
    except Exception as e:
        logger.error(f"Error managing session: {e}")
        # Return a fallback session ID if there's an error
        return f"fallback-{thread_id}-{int(time.time())}"

def invoke_bedrock_agent(text, session_id, thread_id):
    """Invoke Bedrock Agent with the text and session ID."""
    try:
        response = bedrock_agent.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId='TSTALIASID', # Replace with your actual alias ID
            sessionId=session_id,
            inputText=text,
            enableTrace=True
        )
        
        # Get agent's response
        completion = response.get('completion', '')
        
        # Log trace for debugging
        trace = response.get('trace', {})
        logger.info(f"Agent trace for thread {thread_id}: {json.dumps(trace)}")
        
        return completion
    except Exception as e:
        logger.error(f"Error invoking Bedrock agent: {e}")
        return f"I'm having trouble processing your request: {str(e)}"

def post_message_to_slack(token, channel, thread_ts, text):
    """Post a message to Slack channel."""
    client = boto3.client('lambda')
    payload = {
        'token': token,
        'channel': channel,
        'thread_ts': thread_ts,
        'text': text
    }
    
    # Use boto3 HTTP client to post to Slack API
    http = boto3.client('http')
    response = http.request(
        'POST',
        'https://slack.com/api/chat.postMessage',
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {token}'
        },
        body=json.dumps(payload)
    )
    
    return response

def lambda_handler(event, context):
    """Main Lambda handler."""
    try:
        # Get Slack token and signing secret
        slack_token, signing_secret = get_slack_token()
        
        # Verify request is from Slack
        if not verify_slack_request(event, signing_secret):
            logger.warning("Failed to verify Slack request signature")
            return {
                'statusCode': 403,
                'body': json.dumps('Invalid request signature')
            }
        
        # Parse the request body
        body = json.loads(event['body'])
        
        # Handle URL verification challenge
        if body.get('type') == 'url_verification':
            return {
                'statusCode': 200,
                'body': json.dumps({'challenge': body['challenge']})
            }
        
        # Only process message events
        if body.get('event', {}).get('type') != 'message':
            return {
                'statusCode': 200,
                'body': json.dumps('Event type not supported')
            }
        
        # Extract message details
        message_event = body['event']
        channel_id = message_event.get('channel')
        user_id = message_event.get('user')
        text = message_event.get('text', '')
        thread_ts = message_event.get('thread_ts', message_event.get('ts'))
        
        # Check if this is a new thread or reply
        is_in_thread = 'thread_ts' in message_event
        
        # IMPORTANT: Only process messages that explicitly mention our bot, even in threads
        bot_user_id = "<@U12345678>"  # Replace with your actual bot user ID
        if message_event.get('bot_id') or bot_user_id not in text:
            return {
                'statusCode': 200,
                'body': json.dumps('Not a message for this bot')
            }
        
        # Remove the bot mention from the message text
        clean_text = re.sub(f"{bot_user_id}\\s*", "", text).strip()
        
        # Get or create a session for this thread
        session_id = get_or_create_session(thread_ts, channel_id, user_id)
        
        # Invoke Bedrock Agent
        agent_response = invoke_bedrock_agent(clean_text, session_id, thread_ts)
        
        # Post response back to Slack
        post_message_to_slack(slack_token, channel_id, thread_ts, agent_response)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Message processed')
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error')
        }
