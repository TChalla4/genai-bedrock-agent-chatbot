# Slack Webhook Receiver for Amazon Bedrock

## Overview
The **Slack Webhook Receiver** is an AWS Lambda function that receives messages from Slack via the Slack Events API, forwards queries to an Amazon Bedrock Agent for processing, and then sends responses back to the Slack channel. It maintains conversation context across thread-based interactions while requiring explicit @mentions for each interaction.

## Features
- Securely retrieves **Slack bot token** from AWS Secrets Manager
- Listens for **Slack events**, such as bot mentions and messages
- Maintains **conversation context** within Slack threads using DynamoDB session management
- Calls **Amazon Bedrock** for AI-generated responses
- Posts responses back to Slack using the Slack Web API
- Supports **explicit @mention activation** in threads for controlled interactions

## Architecture
1. **Slack sends an event** (e.g., `@zax Hello!`) to an API Gateway
2. **API Gateway invokes the Lambda function**
3. **Lambda checks if the message contains an @mention** of the bot
4. **Lambda retrieves or creates a thread-based session** in DynamoDB
5. **Lambda calls Amazon Bedrock** with the session context for response generation
6. **Lambda posts the response back to Slack** in the same thread
7. **User sees the bot's response in Slack** and can continue the conversation with additional @mentions

## Prerequisites
- **Slack App Setup**:
  - Create a Slack App at [Slack API](https://api.slack.com/apps)
  - Enable **Event Subscriptions** and set the request URL to your API Gateway
  - Subscribe to bot events like `app_mention` and `message.channels`
  - Obtain **Slack Bot Token** and **Signing Secret**
- **AWS Setup**:
  - AWS account with **Lambda, API Gateway, DynamoDB, Secrets Manager, and Bedrock access**
  - Store `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` in **AWS Secrets Manager**
  - Deploy API Gateway with a public endpoint for Slack

## Deployment
### **1. Store Slack Bot Token in AWS Secrets Manager**
Ensure your Slack credentials are stored securely:
```sh
aws secretsmanager create-secret --name slack-integration-secrets \
    --secret-string '{"SLACK_BOT_TOKEN":"xoxb-xxxxxx","SLACK_SIGNING_SECRET":"xxxxx"}'
```

### **2. Deploy the AWS CDK Stack** 
Run the following to deploy the necessary AWS resources:
```sh
./setup.sh
```
The setup script will:

- Deploy Amazon Bedrock Agent stack with knowledge base capabilities
- Deploy Slack Integration stack with session management
- Configure API Gateway for receiving Slack events
- Set up DynamoDB table for session management
- Deploy Lambda function to process and respond to Slack messages
- Store Slack credentials in AWS Secrets Manager

### **3. Configure Slack Events API**
- Go to Slack API Apps → Event Subscriptions
- Enable events and set the Request URL to the API Gateway endpoint from CDK
- Subscribe to events:
  -  app_mention (when the bot is mentioned in a channel)
  -  message.channels (for channel messages)
  -  message.groups (for private channel messages)
- Save changes and deploy the bot to your workspace

### Usage

#### 1. Mention the bot in a channel:
```sh
@zax "What EC2 instance is best for machine learning?"
```

#### 2. Continue the conversation in the thread with explicit @mentions
```sh
@zax "How much does that instance cost?"
```
#### 3. The bot maintains context between @mentions in the same thread 

### Testing

#### 1. Mention the bot in Slack:
```sh
@zax "Hello!" 
```

#### 2. Continue the conversation in the thread with explicit @mentions
```sh
@zax "Tell me more about that."
```
#### 3. Check AWS CloudWatch logs to verify Lambda execution
#### 4. The bot should respond in Slack with context-aware responses from Bedrock

### Security Considerations

 - Secrets Management: All credentials are retrieved securely from AWS Secrets Manager
 - IAM Permissions: The Lambda function has restricted access to only necessary AWS services
 - Slack Verification: The function validates Slack's signatures before processing messages
 - Session Isolation: Each Slack thread maintains its own separate session context
 - Note: This implementation has not undergone security review

### Clean up 

To remove the deployed resources and avoid AWS charges:
```sh
cdk destory
```
Manually delete the S3 bucket if created by CDK.

### Future Enhancements 

- Knowledge contribution system (/teach command) to allow users to add information to the bot's knowledge base
- Verification workflow with a dedicated channel for senior engineers to approve or reject contributed knowledge
- Memory management with automatic expiration of unverified information
- Response templates that clearly indicate verified vs. unverified information sources
- Expand Slack event handling (e.g., commands, reactions)
- Enhance logging & monitoring using AWS CloudWatch
- Improve Bedrock responses with a fine-tuned model
- Knowledge of pipeline status and access to internal tickets titles
- Ticket creation throught slack 
