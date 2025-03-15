# GenAI ChatBot with Amazon Bedrock Agent and Slack Integration

![slackbot](https://github.com/user-attachments/assets/1c1cccba-d804-4f52-bc95-b533fc84c53f)


## Table of Contents

- [Introduction](#Introduction)
- [Prerequisites](#Prerequisites)
- [Target technology stack](#Target-technology-stack)
- [Deployment](#Deployment)
- [Useful CDK commands](#Useful-CDK-commands)
- [Code Structure](#Code-Structure)
- [Customize the chatbot with your own data](#Customize-the-chatbot-with-your-own-data)

## Introduction

This GenAI ChatBot application was built with Amazon Bedrock, which includes KnowledgeBase, Agent, and additional AWS serverless GenAI solutions. The provided solution showcases a Chatbot that makes use of its understanding of EC2 instances and the pricing of EC2 instances. This chatbot functions as an illustration of the capabilities of Amazon Bedrock to convert natural language into Amazon Athena queries and to process and utilize complex data sets. Open source tools, such as LLamaIndex, are utilized to augment the system's capabilities for data processing and retrieval. The integration of several AWS resources is also emphasized in the solution. These resources consist of Amazon S3 for storage, Amazon Bedrock KnowledgeBase to facilitate retrieval augmented generation (RAG), Amazon Bedrock agent to execute multi-step tasks across data sources, AWS Glue to prepare data, Amazon Athena to execute efficient queries, Amazon Lambda to manage containers, and Amazon ECS to oversee containers. The combined utilization of these resources empowers the Chatbot to efficiently retrieve and administer content from databases and documents, thereby demonstrating the capabilities of Amazon Bedrock in the development of advanced Chatbot applications.

### Modifications

This GenAI ChatBot is a serverless, event-driven Slack bot powered by Amazon Bedrock. The bot receives messages from Slack, processes queries using a Bedrock Agent, and responds directly in Slack channels.

#### Includes

- A Slack Webhook Receiver Lambda function
- API Gateway integration for Slack event subscriptions.
- AWS Secrets Manager for storing credentials securely.
- Automated deployment script (setup_assistant.sh) to configure AWS services and Slack integration seamlessly
- Bedrock Agent Invocation for AI-powered responses.

This bot is useful for scenarios where real-time AI-powered responses are needed **in Slack**, such as:
- Customer Support
- Automated Q&A Systems
- DevOps Assistance
- Knowledge Retrievals (RAG) from Amazon Bedrock

## Prerequisites

- Docker
- AWS CDK Toolkit 2.114.1+, installed and configured. For more information, see Getting started with the AWS CDK in the AWS CDK documentation.
- Python 3.11+, installed and configured. For more information, see Beginners Guide/Download in the Python documentation.
- An active AWS account
- An AWS account bootstrapped by using AWS CDK in us-east-1 or us-west-2. Enable Claude model and Titan Embedding model access in Bedrock service.
- Slack App created at Slack API, with:
  - OAuth permissions (`chat:write`, `commands`, `app_mentions:read`, `events:read`).
  - Event Subscriptions enabled.

## Target technology stack

- Amazon Bedrock
- Amazon OpenSearch Serverless
- Amazon ECS
- AWS Glue
- AWS Lambda
- Amazon S3
- Amazon Athena
- Elastic Load Balancer

## Deployment

### Step 1: Run the Setup Assisant 

This project includes an automated setup script that configures everything for you. Run:

```.sh
chmod +x setup.sh
./setup.sh
```

This script:

- Prompts you for required credentials (AWS Region, Slack bot token)
- Stores credentials securely in AWS Secrets Manager
- Deploys the CDK stack (API GW, Lambda, Bedrock, IAM roles)
- Retrieves and stores the Bedrock Agent ID automatically

### Step 2: Configure Slack Webhook 

Once deployment is complete:

- Navigate to your Slack API App settings
- Under Event Subscriptions
- Subscribe to the following events
  `app_mention`
  `message.im`
- Save and deploy

### Step 3: Test the Slack Bot 

- Mention the bot in Slack:
  `@YourBot Hello!`
- The bot should reply with an AI-generated response 

To run the app locally, first add a .env file to 'code/streamlit-app' folder containing the following:

```.env
ACCOUNT_ID = <Your account ID>
AWS_REGION = <Your region>
LAMBDA_FUNCTION_NAME =  invokeAgentLambda # Sets name of choice for the lambda function called by streamlit for a response. Currently invokes an agent.
```

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory. To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```bash
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```bash
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```powershell
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```bash
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```bash
$ cdk synth
```

You will need to bootstrap it if this is your first time running CDK at a particular account and region.

```bash
$ cdk bootstrap
```

Once it's bootstrapped, you can proceed to deploy CDK.

```bash
$ cdk deploy
```

## Useful CDK commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation
- `cdk destroy` destroys one or more specified stacks

## High-level Code Structure

```
code                              # Root folder for code for this solution
├── lambdas                           # Root folder for all lambda functions
│   ├── action-lambda                     # Lambda function that acts as an action for the Amazon Bedrock Agent
│   ├── create-index-lambda               # Lambda function that creates Amazon Opensearch serverless index
│   ├── invoke-lambda                     # Lambda function that invokes Amazon Bedrock Agent
│   ├── slack_webhook                     # Lambda function that processes Slack messages
│   └── update-lambda                     # Lambda function for post-deployment updates
├── layers                            # Root folder for all lambda layers
│   ├── boto3_layer                       # Boto3 layer shared across all lambdas
│   ├── opensearch_layer                  # OpenSearch layer for indexing
├── streamlit-app                         # Streamlit app interface for chatbot
├── setup_assistant.sh                     # Script for setting up secrets and deployment
└── code_stack.py                     # AWS CDK stack that deploys all AWS resources
└── slackbot_stack.py                     # AWS CDK stack that slackbot_architecture
```

## Customize the chatbot with your own data

To integrate your custom data for deploying the solution, follow these steps:

- Upload your dataset to `assets/knowledgebase_data_source/`.
- Update `cdk.json` to reflect new paths.
- Modify `bedrock_instructions` for improved responses.

These steps ensure a seamless and efficient integration process, enabling you to deploy the solution effectively with your data.

