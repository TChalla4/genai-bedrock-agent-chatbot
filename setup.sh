#!/bin/bash

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
    echo "-------------------------------------------------------------"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Welcome message
clear
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}  Amazon Bedrock Slack Integration Setup Tool     ${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "This script will guide you through setting up your Slack integration with Amazon Bedrock."
echo -e "It will deploy both the core Bedrock Agent and the Slack connector.\n"

# Check prerequisites
print_section "Checking Prerequisites"

prereqs_met=true

# Check AWS CLI
if ! command_exists aws; then
    echo -e "${RED}✗ AWS CLI is not installed.${NC} Please install it: https://aws.amazon.com/cli/"
    prereqs_met=false
else
    echo -e "${GREEN}✓ AWS CLI found${NC}"
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &>/dev/null; then
        echo -e "${RED}✗ AWS CLI is not configured properly.${NC} Please run 'aws configure'."
        prereqs_met=false
    else
        echo -e "${GREEN}✓ AWS CLI is configured${NC}"
    fi
fi

# Check CDK
if ! command_exists cdk; then
    echo -e "${RED}✗ AWS CDK is not installed.${NC} Please install it: npm install -g aws-cdk"
    prereqs_met=false
else
    echo -e "${GREEN}✓ AWS CDK found${NC}"
fi

# Check Docker
if ! command_exists docker; then
    echo -e "${YELLOW}! Docker is not installed.${NC} It's required for building Lambda containers."
    prereqs_met=false
else
    echo -e "${GREEN}✓ Docker found${NC}"
fi

# Exit if prerequisites are not met
if [ "$prereqs_met" = false ]; then
    echo -e "\n${RED}Please install the missing prerequisites and run this script again.${NC}"
    exit 1
fi

# Get AWS configuration
print_section "AWS Configuration"
echo "Please provide your AWS configuration details."

read -p "Enter your AWS Region (e.g., us-east-1): " AWS_REGION

# Check if the region is valid
if ! aws ec2 describe-regions --region "$AWS_REGION" --query "Regions[?RegionName=='$AWS_REGION'].RegionName" --output text &>/dev/null; then
    echo -e "${RED}Invalid AWS region.${NC} Please provide a valid region."
    exit 1
fi

# Check if Bedrock is available in the region
if [[ "$AWS_REGION" != "us-east-1" && "$AWS_REGION" != "us-west-2" ]]; then
    echo -e "${YELLOW}Warning: Amazon Bedrock might not be available in $AWS_REGION.${NC}"
    echo "Bedrock is currently available in us-east-1 and us-west-2."
    read -p "Do you want to continue anyway? (y/n): " continue_region
    if [[ "$continue_region" != "y" ]]; then
        echo "Setup canceled. Please run the script again with a supported region."
        exit 1
    fi
fi

# Slack App Configuration
print_section "Slack App Configuration"
echo "Please create a Slack App with the following features:"
echo "1. Bot Token Scopes: chat:write, channels:history, im:history, groups:history"
echo "2. Event Subscriptions: message.channels, message.groups, message.im"
echo "3. Interactive Components: Enable for verification/rejection buttons"
echo -e "${YELLOW}Note: You'll need to update the Request URL after deployment${NC}"

read -p "Enter your Slack Bot Token (starts with 'xoxb-'): " SLACK_BOT_TOKEN
read -p "Enter your Slack Signing Secret: " SLACK_SIGNING_SECRET
read -p "Enter the channel ID for senior engineer notifications (e.g., C12345678): " VERIFICATION_CHANNEL_ID

# Validate Slack token format
if [[ ! $SLACK_BOT_TOKEN =~ ^xoxb- ]]; then
    echo -e "${RED}Invalid Slack Bot Token format.${NC} It should start with 'xoxb-'."
    exit 1
fi

# Memory Management Configuration
print_section "Memory Management Configuration"
echo "Configure how unverified memories are handled:"
read -p "Expiration time for unverified memories in days (default: 7): " MEMORY_EXPIRATION_DAYS
MEMORY_EXPIRATION_DAYS=${MEMORY_EXPIRATION_DAYS:-7}

read -p "Enable daily digest of unverified memories? (y/n, default: y): " ENABLE_DAILY_DIGEST
ENABLE_DAILY_DIGEST=${ENABLE_DAILY_DIGEST:-y}

# Validate memory expiration value
if ! [[ "$MEMORY_EXPIRATION_DAYS" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Invalid expiration time.${NC} Using default: 7 days."
    MEMORY_EXPIRATION_DAYS=7
fi

# Confirm settings
print_section "Configuration Summary"
echo -e "AWS Region: ${YELLOW}$AWS_REGION${NC}"
echo -e "Slack Bot Token: ${YELLOW}[HIDDEN]${NC}"
echo -e "Slack Signing Secret: ${YELLOW}[HIDDEN]${NC}"
echo -e "Verification Channel: ${YELLOW}$VERIFICATION_CHANNEL_ID${NC}"
echo -e "Memory Expiration: ${YELLOW}$MEMORY_EXPIRATION_DAYS days${NC}"
echo -e "Daily Digest: ${YELLOW}$(if [[ "$ENABLE_DAILY_DIGEST" == "y" ]]; then echo "Enabled"; else echo "Disabled"; fi)${NC}"

echo -e "\n${YELLOW}Important:${NC} This setup will deploy both the Bedrock Agent and Slack integration stacks."
read -p "Do you want to proceed with deployment? (y/n): " confirm

if [[ "$confirm" != "y" ]]; then
    echo -e "${RED}Setup canceled.${NC} Please run the script again when ready."
    exit 1
fi

# Store configuration in .env file for reference
print_section "Storing Configuration"
mkdir -p .config

cat > .config/.env << EOF
AWS_REGION=$AWS_REGION
SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET
VERIFICATION_CHANNEL_ID=$VERIFICATION_CHANNEL_ID
MEMORY_EXPIRATION_DAYS=$MEMORY_EXPIRATION_DAYS
ENABLE_DAILY_DIGEST=$ENABLE_DAILY_DIGEST
EOF

echo -e "${GREEN}✓ Configuration stored in .config/.env${NC}"

# Store secrets in AWS Secrets Manager
print_section "Setting up AWS Secrets Manager"
echo "Storing Slack credentials securely..."

# Create a combined secret with all Slack-related values
aws secretsmanager create-secret \
    --name slack-integration-secrets \
    --secret-string "{\"SLACK_BOT_TOKEN\":\"$SLACK_BOT_TOKEN\",\"SLACK_SIGNING_SECRET\":\"$SLACK_SIGNING_SECRET\",\"VERIFICATION_CHANNEL_ID\":\"$VERIFICATION_CHANNEL_ID\"}" \
    --region $AWS_REGION \
    --output json > /dev/null || { echo -e "${RED}Failed to create secret in AWS Secrets Manager${NC}"; exit 1; }

echo -e "${GREEN}✓ Slack credentials stored in AWS Secrets Manager${NC}"

# CDK Deployment
print_section "Deploying AWS CDK Stacks"
echo "This will deploy the following stacks:"
echo "1. BedrockChatbotStack - Core Amazon Bedrock Agent and Knowledge Base"
echo "2. SlackIntegrationStack - Slack connector with session management"
echo -e "${YELLOW}Note: First-time deployment may take 30-45 minutes${NC}"

# Bootstrap CDK if needed
echo "Checking if CDK bootstrap is needed..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &>/dev/null; then
    echo "Bootstrapping CDK in $AWS_REGION..."
    cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION || { echo -e "${RED}CDK bootstrap failed${NC}"; exit 1; }
fi

# Export environment variables for CDK
export CDK_DEPLOY_REGION=$AWS_REGION
export MEMORY_EXPIRATION_DAYS=$MEMORY_EXPIRATION_DAYS
export ENABLE_DAILY_DIGEST=$ENABLE_DAILY_DIGEST

# Deploy the stacks
echo "Deploying CDK stacks..."
cdk deploy --all --require-approval never || { echo -e "${RED}CDK deployment failed${NC}"; exit 1; }

# Capture outputs for Slack app configuration
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name SlackIntegrationStack --region $AWS_REGION --query "Stacks[0].Outputs[?OutputKey=='SlackBotWebhookEndpoint'].OutputValue" --output text)

# Final instructions
print_section "Setup Complete!"
echo -e "${GREEN}Your Amazon Bedrock Slack integration has been successfully deployed!${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Configure your Slack App with the following URLs:"
echo -e "   - Event Subscription Request URL: ${GREEN}${API_ENDPOINT}/webhook${NC}"
echo -e "   - Interactive Components Request URL: ${GREEN}${API_ENDPOINT}/interactive${NC}"
echo ""
echo "2. Invite your bot to channels where it should listen"
echo "3. Use the bot with thread-based conversations:"
echo "   - First message: @yourbot what is the instance type for ML?"
echo "   - Follow-ups in thread: @yourbot can you provide pricing details?"
echo "   - Teaching: /teach [your information]"
echo "   - Note: ALWAYS include @yourbot in every message that needs a response"
echo ""
echo "4. Monitor the verification channel for memory approval requests"

echo -e "\n${BLUE}Documentation:${NC} For more information, see the README.md file"
echo -e "${BLUE}Support:${NC} For issues, please file a ticket in the GitHub repository"

exit 0
