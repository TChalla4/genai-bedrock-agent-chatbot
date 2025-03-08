#!/bin/bash

# Welcome message
echo "Welcome to the Slack Webhook Receiver setup assistant!"
echo "This script will guide you through setting up the necessary environment variables and AWS resources."
echo "-------------------------------------------------------------"

# Prompt user for required variables
echo "Please enter the required variables to set up your application."
read -p "Enter your AWS Region: " AWS_REGION
read -p "Enter your Slack Bot Token: " SLACK_BOT_TOKEN
read -p "Enter your Slack Signing Secret: " SLACK_SIGNING_SECRET

# Confirm values with user
echo "-------------------------------------------------------------"
echo "You have entered the following values:"
echo "AWS Region: $AWS_REGION"
echo "Slack Bot Token: [HIDDEN] (Stored Securely)"
echo "Slack Signing Secret: [HIDDEN] (Stored Securely)"
echo "-------------------------------------------------------------"
read -p "Do you want to proceed with these settings? (y/n): " confirm

if [[ "$confirm" != "y" ]]; then
    echo "Setup canceled. Please run the script again to configure the settings."
    exit 1
fi

# Store environment variables in a .env file
echo "AWS_REGION=$AWS_REGION" > .env
echo "SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN" >> .env
echo "SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET" >> .env

echo "Environment variables stored in .env file."

echo "-------------------------------------------------------------"
echo "Setting up AWS Secrets Manager..."

echo "Storing Slack Bot Token in AWS Secrets Manager..."
aws secretsmanager create-secret --name slack-bot-token --secret-string "{\"SLACK_BOT_TOKEN\":\"$SLACK_BOT_TOKEN\"}" --region $AWS_REGION

echo "Storing Slack Signing Secret in AWS Secrets Manager..."
aws secretsmanager create-secret --name slack-signing-secret --secret-string "{\"SLACK_SIGNING_SECRET\":\"$SLACK_SIGNING_SECRET\"}" --region $AWS_REGION

echo "-------------------------------------------------------------"
echo "Deploying AWS CDK Stack..."
cdk deploy

# Fetch the Bedrock Agent ID after deployment
BEDROCK_AGENT_ID=$(aws cloudformation describe-stacks --stack-name SlackBotStack --query "Stacks[0].Outputs[?OutputKey=='BedrockAgentID'].OutputValue" --output text)

echo "-------------------------------------------------------------"
echo "Storing Bedrock Agent ID in AWS Secrets Manager..."
aws secretsmanager create-secret --name bedrock-agent-id --secret-string "{\"BEDROCK_AGENT_ID\":\"$BEDROCK_AGENT_ID\"}" --region $AWS_REGION

echo "-------------------------------------------------------------"
echo "Setup complete! Your application is now configured and deployed."
echo "Check the AWS Console and Slack App settings to verify connectivity."
exit 0
