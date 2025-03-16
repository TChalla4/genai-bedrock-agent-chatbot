### **🔹 Updated README Based on Your Feedback**  

I've **corrected** the knowledge base part (since the backend **does** support it), **clarified session handling**, and **removed the "memory expiration" feature** that isn’t implemented yet.

---

# **Slack Webhook Receiver for Amazon Bedrock**
## **Overview**
The Slack Webhook Receiver is an AWS Lambda function that receives messages from Slack via the Slack Events API, forwards queries to an Amazon Bedrock Agent for processing, and then sends responses back to the Slack channel. **It tracks conversations within Slack threads using DynamoDB session management and integrates with an Amazon Bedrock Knowledge Base to enhance responses.** The bot requires explicit `@mentions` for each interaction.

## **Features**
- **Retrieves Slack bot token securely from AWS Secrets Manager**
- **Listens for Slack events (mentions and messages in public/private channels)**
- **Tracks conversation sessions within Slack threads using DynamoDB**
- **Calls Amazon Bedrock for AI-generated responses, enhanced with a backend Knowledge Base**
- **Posts responses back to Slack in the same thread**
- **Supports explicit `@mention` activation to prevent unwanted responses**

## **Architecture**
1. Slack sends an event (e.g., `@zax Hello!`) to an API Gateway.  
2. API Gateway invokes the Lambda function.  
3. Lambda verifies if the message contains an `@mention` of the bot.  
4. Lambda retrieves or creates a thread-based session in DynamoDB.  
5. **Lambda calls Amazon Bedrock, leveraging a backend Knowledge Base for contextual answers.**  
6. Lambda posts the response back to Slack in the same thread.  
7. **User must mention the bot again for each new response.**  

## **Prerequisites**
### **Slack App Setup**
- **Create a Slack App in the Slack API Dashboard.**  
- **Enable Event Subscriptions and set the request URL to your API Gateway.**  
- **Subscribe to bot events like `app_mention` and `message.channels`.**  
- **Obtain a Slack Bot Token and Signing Secret.**  

### **AWS Setup**
- **AWS account with access to Lambda, API Gateway, DynamoDB, Secrets Manager, and Bedrock.**  
- **Store `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` securely in AWS Secrets Manager.**  
- **Deploy API Gateway with a public endpoint for Slack webhook integration.**  

---

## **Deployment**
### **1. Store Slack Bot Token in AWS Secrets Manager**
```sh
aws secretsmanager create-secret --name slack-integration-secrets \
    --secret-string '{"SLACK_BOT_TOKEN":"xoxb-xxxxxx","SLACK_SIGNING_SECRET":"xxxxx"}'
```

### **2. Deploy the AWS CDK Stack**
```sh
./setup.sh
```
The setup script will:
- **Deploy API Gateway for receiving Slack events**
- **Deploy a Lambda function for processing Slack messages**
- **Create a DynamoDB table for session management**
- **Store Slack credentials in AWS Secrets Manager**
- **Enable Amazon Bedrock for AI responses**
- **Deploy an Amazon Bedrock Knowledge Base to enhance responses with contextual data**  

### **3. Configure Slack Events API**
1. **Go to Slack API Apps → Event Subscriptions**  
2. **Enable events and set the Request URL to the API Gateway endpoint from CDK**  
3. **Subscribe to events:**  
   - `app_mention` (when the bot is mentioned in a channel)  
   - `message.channels` (for channel messages)  
   - `message.groups` (for private channel messages)  
4. **Save changes and deploy the bot to your workspace**  

---

## **Usage**
1. **Mention the bot in a channel:**  
   ```@zax "What EC2 instance is best for machine learning?"```
2. **Continue the conversation in the thread with explicit `@mentions`**  
   ```@zax "How much does that instance cost?"```  
3. **The bot tracks context per Slack thread but does not maintain long-term memory across conversations.**  
4. **Responses may be enhanced with relevant knowledge from the backend Amazon Bedrock Knowledge Base.**  

---

## **Testing**
1. **Mention the bot in Slack:**  
   ```@zax "Hello!"```  
2. **Continue the conversation with `@mentions`.**  
3. **Check AWS CloudWatch logs to verify Lambda execution.**  
4. **The bot should respond in Slack with context-aware responses from Bedrock.**  

---

## **Security Considerations**
- ✅ **Secrets Management:** Retrieves credentials securely from AWS Secrets Manager.  
- ✅ **IAM Permissions:** Lambda has restricted access to only required AWS services.  
- ✅ **Slack Verification:** Requests are validated before processing.  
- ✅ **Session Isolation:** Each Slack thread maintains its own session in DynamoDB.  
- ⚠️ **Note:** This implementation has not undergone a formal security review.  

---

## **Clean up**
To remove the deployed resources and avoid AWS charges:
```sh
cdk destroy
```
Manually delete the S3 bucket if CDK created one.

---

## **Future Enhancements**
🚀 **Knowledge contribution system (`/teach` command) to allow users to add info to the bot’s database**  
🚀 **Approval workflow for knowledge contributions**  
🚀 **Better memory across conversations (right now, it tracks per-thread only)**  
🚀 **Expanded event handling (`/commands`, reactions, etc.)**  
🚀 **Logging & monitoring improvements using AWS CloudWatch**  
🚀 **Bedrock fine-tuning for improved responses**  
🚀 **Ticket creation through Slack**  
