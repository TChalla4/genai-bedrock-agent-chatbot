from aws_cdk import (
    core as cdk,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager
)

class SlackBotStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create an IAM role for Lambda
        lambda_role = iam.Role(
            self, "SlackBotLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Allow Lambda to call Bedrock and post to Slack API
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeAgent"],
            resources=["*"]  # Replace with specific Bedrock agent ARN if possible
        ))

        # Store Slack Bot Token securely
        slack_secret = secretsmanager.Secret(self, "SlackBotToken",
            secret_name="slack-bot-token",
            description="Slack Bot Token for API Integration"
        )

        # Create the Lambda function for webhook processing
        slack_lambda = lambda_.Function(
            self, "SlackBotLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            role=lambda_role,
            environment={
                "SLACK_SECRET_ARN": slack_secret.secret_arn,
                "BEDROCK_AGENT_ID": "your-bedrock-agent-id",  # Replace with actual Bedrock agent ID
                "AWS_REGION": self.region
            },
        )

        # Grant Lambda permission to read from Secrets Manager
        slack_secret.grant_read(slack_lambda)

        # API Gateway for webhook endpoint
        api = apigateway.RestApi(
            self, "SlackBotAPI",
            rest_api_name="Slack Bot API",
            description="API Gateway for Slack Webhook Receiver"
        )

        webhook_resource = api.root.add_resource("webhook")
        webhook_resource.add_method("POST", apigateway.LambdaIntegration(slack_lambda))

        # Output API Gateway endpoint
        cdk.CfnOutput(
            self, "SlackBotWebhookEndpoint",
            value=api.url,
            description="Slack Bot Webhook API Endpoint"
        )
