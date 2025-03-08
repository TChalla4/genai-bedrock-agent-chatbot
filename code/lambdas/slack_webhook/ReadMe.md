# Slack Webhook Receiver

## Overview
The **Slack Webhook Receiver** is an AWS Lambda function that receives messages from Slack via the Slack Events API, forwards queries to an Amazon Bedrock Agent for processing, and then sends responses back to the Slack channel.

## Features
- Securely retrieves **Slack bot token** from AWS Secrets Manager.
- Listens for **Slack events**, such as bot mentions and messages.
- Calls **Amazon Bedrock** for AI-generated responses.
- Posts responses back to Slack using the Slack Web API.

## Architecture
1. **Slack sends an event** (e.g., `@bot_name Hello!`) to an API Gateway.
2. **API Gateway invokes the Lambda function**.
3. **Lambda extracts the message & calls Amazon Bedrock** for response generation.
4. **Lambda posts the response back to Slack**.
5. **User sees the bot’s response in Slack**.

## Prerequisites
- **Slack App Setup**:
  - Create a Slack App at [Slack API](https://api.slack.com/apps).
  - Enable **Event Subscriptions** and set the request URL to your API Gateway.
  - Subscribe to bot events like `app_mention` and `message.im`.
  - Obtain **Slack Bot Token** and **Signing Secret**.
- **AWS Setup**:
  - AWS account with **Lambda, API Gateway, Secrets Manager, and Bedrock access**.
  - Store `SLACK_BOT_TOKEN` in **AWS Secrets Manager**.
  - Deploy API Gateway with a public endpoint for Slack.

## Deployment
### **1. Store Slack Bot Token in AWS Secrets Manager**
Ensure your Slack bot token is stored securely:
```sh
aws secretsmanager create-secret --name slack-bot-token --secret-string '{"SLACK_BOT_TOKEN":"xoxb-xxxxxx"}'
```

### **2. Deploy the AWS CDK Stack**
Run the following to deploy the necessary AWS resources:
```sh
cdk deploy
```
The CDK stack will:
- Deploy **API Gateway** for receiving Slack events.
- Deploy **Lambda function** to process and respond to Slack messages.
- Store **Slack bot token** in AWS Secrets Manager.

### **3. Configure Slack Events API**
- Go to **Slack API Apps → Event Subscriptions**.
- Enable events and set the **Request URL** to the API Gateway endpoint from CDK.
- Subscribe to events:
  - `app_mention` (when the bot is mentioned in a channel).
  - `message.im` (for direct messages to the bot).
- Save changes and deploy the bot to your workspace.

## Testing
1. **Mention the bot in Slack**:
   ```
   @YourBot Hello!
   ```
2. **Check AWS CloudWatch logs** to verify Lambda execution.
3. **The bot should respond in Slack** with a generated message from Bedrock.

## Security Considerations
- **Secrets Management**: The bot token is retrieved securely from AWS Secrets Manager.
- **IAM Permissions**: The Lambda function has restricted access to only necessary AWS services.
- **Slack Verification**: The function validates Slack’s challenge requests before processing messages.

## Cleanup
To remove the deployed resources and avoid AWS charges:
```sh
cdk destroy
```
Manually delete the **S3 bucket** if created by CDK.

## Future Enhancements
- **Expand Slack event handling** (e.g., commands, reactions).
- **Enhance logging & monitoring** using AWS CloudWatch.
- **Improve Bedrock responses** with a fine-tuned model.

## Support
For issues, check CloudWatch logs and ensure your Slack bot has the correct permissions. If needed, reconfigure the API Gateway URL in Slack's Event Subscriptions.

