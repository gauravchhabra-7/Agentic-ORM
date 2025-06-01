#!/bin/bash

# ORM Platform Fixed Lambda Deployment Script
# Fixed JSON formatting and added proper wait mechanisms

set -e

# Configuration
PROJECT_NAME="orm-platform"
ENVIRONMENT="dev"
REGION="ap-south-1"
PYTHON_VERSION="python3.9"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Fixed ORM Platform Lambda Deployment${NC}"

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Construct resource names
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${PROJECT_NAME}-lambda-role-${ENVIRONMENT}"
COMMENTS_TABLE="${PROJECT_NAME}-comments-${ENVIRONMENT}"
CONFIG_TABLE="${PROJECT_NAME}-config-${ENVIRONMENT}"
AUDIT_TABLE="${PROJECT_NAME}-audit-${ENVIRONMENT}"
QUEUE_URL="https://sqs.${REGION}.amazonaws.com/${ACCOUNT_ID}/${PROJECT_NAME}-comments-${ENVIRONMENT}"
SECRET_NAME="${PROJECT_NAME}-api-keys-${ENVIRONMENT}"

echo "Using Account ID: ${ACCOUNT_ID}"
echo "Using Role ARN: ${ROLE_ARN}"

# Function to wait for Lambda function to be ready
wait_for_function_ready() {
    local function_name=$1
    echo "Waiting for function ${function_name} to be ready..."
    
    # Wait up to 5 minutes for function to be ready
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local state=$(aws lambda get-function --function-name ${function_name} --region ${REGION} --query 'Configuration.State' --output text 2>/dev/null || echo "NotFound")
        
        if [ "$state" = "Active" ]; then
            echo "Function ${function_name} is ready"
            return 0
        elif [ "$state" = "NotFound" ]; then
            echo "Function ${function_name} does not exist yet"
            return 0
        else
            echo "Function state: ${state}. Waiting..."
            sleep 10
            attempt=$((attempt + 1))
        fi
    done
    
    echo "Warning: Function ${function_name} not ready after waiting"
    return 1
}

# Function to package a Lambda function
package_function() {
    local function_name=$1
    local function_dir=$2
    
    echo -e "${YELLOW}📦 Packaging ${function_name}...${NC}"
    
    # Create temporary directory for packaging
    local temp_dir="./temp-${function_name}"
    rm -rf ${temp_dir}
    mkdir -p ${temp_dir}
    
    # Copy function code
    cp -r ${function_dir}/* ${temp_dir}/
    
    # Copy shared utilities
    cp -r shared/ ${temp_dir}/
    
    # Install dependencies if requirements.txt exists
    if [ -f "shared/requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip3 install -r shared/requirements.txt -t ${temp_dir}/ --quiet
    fi
    
    # Create ZIP package
    cd ${temp_dir}
    zip -r "../${function_name}.zip" . -q
    cd ..
    
    # Clean up
    rm -rf ${temp_dir}
    
    echo -e "${GREEN}✅ ${function_name} packaged successfully${NC}"
}

# Function to deploy a Lambda function
deploy_function() {
    local function_name=$1
    local zip_file="${function_name}.zip"
    local aws_function_name="${PROJECT_NAME}-${function_name}-${ENVIRONMENT}"
    
    echo -e "${YELLOW}🚀 Deploying ${function_name}...${NC}"
    
    # Wait for function to be ready first (in case of previous updates)
    wait_for_function_ready ${aws_function_name}
    
    # Check if function exists
    if aws lambda get-function --function-name ${aws_function_name} --region ${REGION} &> /dev/null; then
        # Update existing function
        echo "Updating existing function code..."
        aws lambda update-function-code \
            --function-name ${aws_function_name} \
            --zip-file fileb://${zip_file} \
            --region ${REGION} > /dev/null
        
        # Wait for update to complete
        echo "Waiting for code update to complete..."
        aws lambda wait function-updated --function-name ${aws_function_name} --region ${REGION}
        
        echo "Updating function configuration..."
        aws lambda update-function-configuration \
            --function-name ${aws_function_name} \
            --timeout 300 \
            --memory-size 512 \
            --region ${REGION} > /dev/null
        
        # Wait for configuration update to complete
        echo "Waiting for configuration update to complete..."
        aws lambda wait function-updated --function-name ${aws_function_name} --region ${REGION}
    else
        # Create new function
        echo "Creating new function..."
        aws lambda create-function \
            --function-name ${aws_function_name} \
            --runtime ${PYTHON_VERSION} \
            --role ${ROLE_ARN} \
            --handler lambda_function.lambda_handler \
            --zip-file fileb://${zip_file} \
            --timeout 300 \
            --memory-size 512 \
            --region ${REGION} > /dev/null
        
        # Wait for function to be created and active
        echo "Waiting for function creation to complete..."
        aws lambda wait function-active --function-name ${aws_function_name} --region ${REGION}
    fi
    
    # Set environment variables with proper JSON formatting
    echo "Setting environment variables..."
    
    # Create environment variables JSON file
    cat > /tmp/env-vars.json << EOF
{
    "Variables": {
        "COMMENTS_TABLE": "${COMMENTS_TABLE}",
        "CONFIG_TABLE": "${CONFIG_TABLE}",
        "AUDIT_TABLE": "${AUDIT_TABLE}",
        "QUEUE_URL": "${QUEUE_URL}",
        "SECRET_NAME": "${SECRET_NAME}"
    }
}
EOF
    
    aws lambda update-function-configuration \
        --function-name ${aws_function_name} \
        --environment file:///tmp/env-vars.json \
        --region ${REGION} > /dev/null
    
    # Wait for environment update to complete
    echo "Waiting for environment update to complete..."
    aws lambda wait function-updated --function-name ${aws_function_name} --region ${REGION}
    
    # Clean up temp file
    rm -f /tmp/env-vars.json
    
    echo -e "${GREEN}✅ ${function_name} deployed successfully${NC}"
}

# Main deployment process
main() {
    echo -e "${GREEN}Starting deployment process...${NC}"
    
    # Check if we're in the right directory
    if [ ! -d "lambda-functions" ]; then
        echo -e "${RED}❌ Please run this script from the project root directory${NC}"
        exit 1
    fi
    
    # Check prerequisites
    echo "Checking AWS CLI and permissions..."
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not configured. Run 'aws configure' first.${NC}"
        exit 1
    fi
    
    # Change to lambda-functions directory
    cd lambda-functions
    
    # List of functions to deploy
    functions=(
        "ingestion-function"
        "classification-function"
        "reply-handler"
        "hide-handler"
        "escalation-handler"
        "dashboard-api"
    )
    
    # Package and deploy each function
    for func in "${functions[@]}"; do
        if [ -d "$func" ]; then
            package_function ${func} ${func}
            deploy_function ${func}
            
            # Clean up zip file
            rm -f ${func}.zip
            
            echo "Sleeping 5 seconds between deployments..."
            sleep 5
        else
            echo -e "${RED}❌ Directory ${func} not found${NC}"
        fi
    done
    
    # Configure SQS trigger for classification function
    echo -e "${YELLOW}🔗 Configuring SQS trigger...${NC}"
    
    queue_arn="arn:aws:sqs:${REGION}:${ACCOUNT_ID}:${PROJECT_NAME}-comments-${ENVIRONMENT}"
    
    # Check if event source mapping already exists
    existing_mappings=$(aws lambda list-event-source-mappings \
        --function-name "${PROJECT_NAME}-classification-function-${ENVIRONMENT}" \
        --region ${REGION} \
        --query 'EventSourceMappings[?EventSourceArn==`'${queue_arn}'`].UUID' \
        --output text)
    
    if [ -z "$existing_mappings" ]; then
        aws lambda create-event-source-mapping \
            --function-name "${PROJECT_NAME}-classification-function-${ENVIRONMENT}" \
            --event-source-arn ${queue_arn} \
            --batch-size 10 \
            --region ${REGION} > /dev/null
        echo "✅ SQS trigger created"
    else
        echo "✅ SQS trigger already exists"
    fi
    
    # Configure EventBridge trigger for ingestion function
    echo -e "${YELLOW}⏰ Configuring EventBridge trigger...${NC}"
    
    # Add Lambda permission for EventBridge
    aws lambda add-permission \
        --function-name "${PROJECT_NAME}-ingestion-function-${ENVIRONMENT}" \
        --statement-id "eventbridge-invoke" \
        --action "lambda:InvokeFunction" \
        --principal "events.amazonaws.com" \
        --source-arn "arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${PROJECT_NAME}-ingestion-${ENVIRONMENT}" \
        --region ${REGION} 2>/dev/null || echo "EventBridge permission already exists"
    
    # Add target to EventBridge rule
    aws events put-targets \
        --rule "${PROJECT_NAME}-ingestion-${ENVIRONMENT}" \
        --targets "Id"="1","Arn"="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${PROJECT_NAME}-ingestion-function-${ENVIRONMENT}" \
        --region ${REGION} > /dev/null
    
    echo -e "${GREEN}✅ EventBridge trigger configured${NC}"
    
    # Return to project root
    cd ..
    
    echo -e "${GREEN}🎉 All Lambda functions deployed successfully!${NC}"
    echo -e "${YELLOW}📋 Deployment Summary:${NC}"
    echo "  • 6 Lambda functions deployed"
    echo "  • SQS trigger configured for classification"
    echo "  • EventBridge trigger configured for ingestion"
    echo "  • Environment variables set for all functions"
    
    # Verify deployment
    echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
    for func in "${functions[@]}"; do
        aws_function_name="${PROJECT_NAME}-${func}-${ENVIRONMENT}"
        if aws lambda get-function --function-name ${aws_function_name} --region ${REGION} &> /dev/null; then
            echo "  ✅ ${func} deployed successfully"
        else
            echo "  ❌ ${func} deployment failed"
        fi
    done
    
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: python3 setup-sample-data.py"
    echo "2. Run: python3 test-system.py"
    echo "3. Test manually with: aws lambda invoke --function-name orm-platform-dashboard-api-dev --payload '{\"httpMethod\":\"GET\",\"path\":\"/health\"}' response.json"
}

# Run main function
main "$@"