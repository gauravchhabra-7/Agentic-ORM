# ORM Platform MVP - Complete Deployment Guide

🚀 **Agentic Online Reputation Management Platform**

This guide will take you from zero to a fully functional ORM platform in **24 hours**.

## 🎯 What You'll Build

- **Automated comment ingestion** from Meta ads (Facebook & Instagram)
- **AI-powered classification** using OpenAI GPT-4o-mini
- **Smart actions**: Auto-reply, hide toxic content, escalate complaints
- **Real-time dashboard** with analytics and monitoring
- **Audit trail** for compliance and analytics
- **Multi-client support** with configurable rules

## 📋 Prerequisites

### Required Accounts
- ✅ AWS Account (free tier eligible)
- ✅ OpenAI API Account ($5-10 credit)
- ✅ Meta Developer Account (Facebook Business)
- ✅ Slack Workspace (for notifications)

### Required Software
- ✅ macOS/Linux terminal
- ✅ Python 3.9+
- ✅ Terraform
- ✅ AWS CLI
- ✅ VS Code (recommended)

## 🏗️ Architecture Overview

```
Meta API → EventBridge → Ingestion Lambda → SQS → Classification Lambda → Actions
                                                      ↓
Dashboard ← API Gateway ← Dashboard Lambda ← DynamoDB (Comments/Config/Audit)
                                                      ↓
                                         Slack/Email ← Escalation Lambda
```

## 🚀 Deployment Steps

### Phase 1: Infrastructure Setup (Hours 1-2)

1. **Clone and Setup Project**
   ```bash
   mkdir ~/orm-platform-mvp
   cd ~/orm-platform-mvp
   
   # Create folder structure
   mkdir infrastructure lambda-functions dashboard docs
   mkdir lambda-functions/{shared,ingestion-function,classification-function,reply-handler,hide-handler,escalation-handler,dashboard-api}
   ```

2. **Configure AWS**
   ```bash
   # Install AWS CLI (if not done)
   brew install awscli
   
   # Configure credentials
   aws configure
   # Enter: Access Key, Secret Key, ap-south-1, json
   
   # Test connection
   aws sts get-caller-identity
   ```

3. **Deploy Infrastructure**
   ```bash
   cd infrastructure
   
   # Save the main.tf file (provided in artifacts)
   # Save the terraform.tfvars file
   
   # Initialize and deploy
   terraform init
   terraform plan
   terraform apply  # Type 'yes' when prompted
   
   # Save outputs
   terraform output > ../docs/aws-resources.txt
   ```

4. **Update API Keys**
   ```bash
   # Update secrets with your real API keys
   aws secretsmanager update-secret \
     --secret-id orm-platform-api-keys-dev \
     --region ap-south-1 \
     --secret-string '{
       "openai_api_key": "sk-your-actual-openai-key",
       "meta_app_id": "your-facebook-app-id",
       "meta_app_secret": "your-facebook-app-secret",
       "meta_access_token": "your-facebook-access-token",
       "slack_webhook_url": "https://hooks.slack.com/your-webhook"
     }'
   ```

### Phase 2: Lambda Functions (Hours 3-4)

1. **Create Function Files**
   ```bash
   cd ../lambda-functions
   
   # Copy all the Lambda function code from artifacts:
   # - shared/utils.py
   # - shared/requirements.txt
   # - ingestion-function/lambda_function.py
   # - classification-function/lambda_function.py
   # - reply-handler/lambda_function.py
   # - hide-handler/lambda_function.py
   # - escalation-handler/lambda_function.py
   # - dashboard-api/lambda_function.py
   ```

2. **Deploy Lambda Functions**
   ```bash
   # Make deployment script executable
   chmod +x ../deploy-lambdas.sh
   
   # Deploy all functions
   ../deploy-lambdas.sh
   ```

### Phase 3: Sample Data & Testing (Hours 5-6)

1. **Setup Sample Data**
   ```bash
   cd ..
   
   # Run sample data setup
   python3 setup-sample-data.py
   ```

2. **Test System**
   ```bash
   # Run comprehensive tests
   python3 test-system.py
   ```

### Phase 4: Dashboard & Final Setup (Hours 7-8)

1. **Verify All Components**
   ```bash
   # Check Lambda functions
   aws lambda list-functions --region ap-south-1 | grep orm-platform
   
   # Check DynamoDB tables
   aws dynamodb list-tables --region ap-south-1
   
   # Test dashboard API
   aws lambda invoke --function-name orm-platform-dashboard-api-dev \
     --payload '{"httpMethod":"GET","path":"/health"}' \
     --region ap-south-1 response.json
   
   cat response.json
   ```

2. **Configure Meta API Integration**
   - Update the sample client config with your actual Facebook Page ID
   - Update with your Ad Account ID
   - Test comment ingestion manually

## 📊 Testing Your MVP

### 1. Health Check
```bash
# Test infrastructure health
aws lambda invoke --function-name orm-platform-dashboard-api-dev \
  --payload '{"httpMethod":"GET","path":"/health"}' \
  --region ap-south-1 health.json && cat health.json
```

### 2. Manual Comment Processing
```bash
# Trigger ingestion manually
aws lambda invoke --function-name orm-platform-ingestion-function-dev \
  --payload '{"source":"aws.events","detail-type":"Scheduled Event"}' \
  --region ap-south-1 ingestion.json
```

### 3. Test Classification
```bash
# Test with sample comment
aws lambda invoke --function-name orm-platform-classification-function-dev \
  --payload '{"Records":[{"body":"{\"action\":\"classify_comment\",\"comment_id\":\"test_123\",\"client_id\":\"demo_client_001\"}"}]}' \
  --region ap-south-1 classification.json
```

## 🔧 Configuration

### Client Onboarding

1. **Add New Client Configuration**
   ```python
   # Use the sample data script as template
   # Update with client-specific:
   # - Facebook Page ID
   # - Ad Account ID
   # - Response templates
   # - Business rules
   ```

2. **Response Templates**
   ```json
   {
     "question": "Hi {name}! Thanks for your question...",
     "complaint": "Hi {name}, we're sorry to hear...",
     "positive": "Thanks for the feedback, {name}!",
     "default": "Thank you for your comment..."
   }
   ```

3. **Classification Rules**
   ```json
   {
     "toxicity_threshold": 7,
     "auto_reply_enabled": true,
     "urgency_keywords": ["urgent", "broken", "asap"],
     "business_context": "Your business description"
   }
   ```

## 📈 Monitoring & Analytics

### Dashboard Endpoints

- **Health**: `GET /health`
- **Metrics**: `GET /metrics?client_id=demo_client_001`
- **Comments**: `GET /comments?client_id=demo_client_001`
- **Configuration**: `GET /config/demo_client_001`
- **Audit Logs**: `GET /audit?client_id=demo_client_001`

### Key Metrics

- Total comments processed
- Sentiment breakdown (positive/negative/neutral)
- Action breakdown (replied/hidden/escalated)
- Response times
- Platform breakdown (Facebook/Instagram/Ads)

## 🚨 Monitoring & Alerts

### CloudWatch Alarms
- Lambda function errors
- DynamoDB throttling
- SQS message age
- API Gateway errors

### Slack Notifications
- High-priority comments
- Hidden toxic content
- System errors
- Daily summaries

## 💰 Cost Optimization

### Free Tier Usage (First 12 months)
- **Lambda**: 1M requests/month (covers ~33k comments/day)
- **DynamoDB**: 25 RCU/WCU (handles ~2M operations/month)
- **API Gateway**: 1M requests/month
- **CloudWatch**: 10 custom metrics

### Estimated Monthly Cost After Free Tier
- **MVP (1K comments/day)**: $10-30/month
- **Growth (10K comments/day)**: $50-100/month
- **Scale (100K comments/day)**: $200-500/month

## 🔒 Security Checklist

- ✅ API keys stored in AWS Secrets Manager
- ✅ IAM roles with least-privilege access
- ✅ VPC endpoints for private communication
- ✅ Encryption at rest and in transit
- ✅ Audit logging for all actions
- ✅ Rate limiting on API endpoints

## 🐛 Troubleshooting

### Common Issues

1. **Lambda Timeout**
   - Increase timeout in function configuration
   - Optimize OpenAI API calls

2. **DynamoDB Throttling**
   - Switch to on-demand billing
   - Implement exponential backoff

3. **Meta API Rate Limits**
   - Implement request queuing
   - Use batch API calls

4. **Classification Accuracy**
   - Improve prompts
   - Add client-specific keywords
   - Fine-tune confidence thresholds

### Debug Commands

```bash
# Check Lambda logs
aws logs tail /aws/lambda/orm-platform-classification-dev --follow

# Check SQS messages
aws sqs receive-message --queue-url $(terraform output -raw sqs_queue_url)

# Verify DynamoDB data
aws dynamodb scan --table-name orm-platform-comments-dev --limit 5
```

## 🚀 Next Steps: Scaling to Production

### Phase 2 Features (Week 2-4)
- [ ] Multi-tenant dashboard
- [ ] Advanced analytics
- [ ] Custom model training
- [ ] Email integration
- [ ] SMS notifications
- [ ] Competitor monitoring

### Phase 3 Features (Month 2-3)
- [ ] White-label solution
- [ ] API for clients
- [ ] Mobile app
- [ ] Advanced AI models
- [ ] Integration marketplace

## 📞 Support

### Getting Help
1. **AWS Issues**: Check AWS documentation
2. **OpenAI Issues**: Check OpenAI status page
3. **Meta API Issues**: Check Meta Developer docs
4. **System Issues**: Run the test script

### Performance Optimization
1. Monitor CloudWatch metrics
2. Optimize Lambda memory allocation
3. Use DynamoDB batch operations
4. Implement caching for frequent queries

---

## 🎉 Congratulations!

You now have a fully functional Agentic ORM platform that can:
- ✅ Monitor thousands of comments automatically
- ✅ Classify and respond intelligently
- ✅ Hide toxic content instantly
- ✅ Escalate important issues
- ✅ Provide real-time analytics
- ✅ Scale with your business

**Your MVP is complete and ready for clients!** 🚀

---

*Built with ❤️ for modern digital businesses*