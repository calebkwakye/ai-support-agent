#!/bin/bash

# ==============================================================================
# AWS Deployment Script for AI Support Agent
# ==============================================================================
# This script deploys the agent to AWS Lambda with API Gateway and DynamoDB.
# 
# Prerequisites:
#   - AWS CLI configured with credentials
#   - Python 3.9+ installed
#   - OpenAI API key
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
# ==============================================================================

set -e  # Exit on any error

# Configuration
FUNCTION_NAME="ai-support-agent"
TABLE_NAME="ai-support-conversations"
REGION="us-east-1"
RUNTIME="python3.11"
TIMEOUT=30
MEMORY=256

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AI Support Agent - AWS Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    # Try to load from .env file
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY not set${NC}"
    echo "Please set it: export OPENAI_API_KEY=your-key-here"
    exit 1
fi

echo -e "${GREEN}✓${NC} OpenAI API key found"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓${NC} AWS Account: $ACCOUNT_ID"

# ==============================================================================
# Step 1: Create DynamoDB Table
# ==============================================================================
echo ""
echo -e "${YELLOW}Step 1: Creating DynamoDB table...${NC}"

# Check if table exists
if aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Table '$TABLE_NAME' already exists"
else
    aws dynamodb create-table \
        --table-name $TABLE_NAME \
        --attribute-definitions AttributeName=conversation_id,AttributeType=S \
        --key-schema AttributeName=conversation_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION
    
    echo "Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
    echo -e "${GREEN}✓${NC} Table '$TABLE_NAME' created"
fi

# ==============================================================================
# Step 2: Create IAM Role for Lambda
# ==============================================================================
echo ""
echo -e "${YELLOW}Step 2: Creating IAM role...${NC}"

ROLE_NAME="${FUNCTION_NAME}-role"

# Trust policy for Lambda
TRUST_POLICY='{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}'

# Check if role exists
if aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Role '$ROLE_NAME' already exists"
else
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document "$TRUST_POLICY"
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    # Create and attach DynamoDB policy
    DYNAMODB_POLICY="{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Effect\": \"Allow\",
                \"Action\": [
                    \"dynamodb:GetItem\",
                    \"dynamodb:PutItem\",
                    \"dynamodb:UpdateItem\",
                    \"dynamodb:DeleteItem\",
                    \"dynamodb:Scan\"
                ],
                \"Resource\": \"arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$TABLE_NAME\"
            }
        ]
    }"
    
    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name "${FUNCTION_NAME}-dynamodb-policy" \
        --policy-document "$DYNAMODB_POLICY"
    
    echo -e "${GREEN}✓${NC} Role '$ROLE_NAME' created"
    
    # Wait for role to propagate
    echo "Waiting for IAM role to propagate..."
    sleep 10
fi

ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

# ==============================================================================
# Step 3: Package Lambda Function
# ==============================================================================
echo ""
echo -e "${YELLOW}Step 3: Packaging Lambda function...${NC}"

# Create a temporary directory for packaging
PACKAGE_DIR=$(mktemp -d)
echo "Package directory: $PACKAGE_DIR"

# Install dependencies for Linux (Lambda runs on Amazon Linux)
pip install --target $PACKAGE_DIR \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    openai python-dotenv --quiet

# Copy our code
cp agent.py $PACKAGE_DIR/
cp database.py $PACKAGE_DIR/
cp lambda_handler.py $PACKAGE_DIR/

# Create deployment package
cd $PACKAGE_DIR
zip -r9 ../deployment-package.zip . -x "*.pyc" -x "__pycache__/*" > /dev/null
cd -

mv $PACKAGE_DIR/../deployment-package.zip ./deployment-package.zip
rm -rf $PACKAGE_DIR

PACKAGE_SIZE=$(ls -lh deployment-package.zip | awk '{print $5}')
echo -e "${GREEN}✓${NC} Package created: deployment-package.zip ($PACKAGE_SIZE)"

# ==============================================================================
# Step 4: Create/Update Lambda Function
# ==============================================================================
echo ""
echo -e "${YELLOW}Step 4: Deploying Lambda function...${NC}"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://deployment-package.zip \
        --region $REGION > /dev/null
    
    # Wait for update to complete
    aws lambda wait function-updated --function-name $FUNCTION_NAME --region $REGION
    
    # Update configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --environment "Variables={OPENAI_API_KEY=$OPENAI_API_KEY,DYNAMODB_TABLE=$TABLE_NAME}" \
        --region $REGION > /dev/null
    
    echo -e "${GREEN}✓${NC} Function updated"
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler lambda_handler.lambda_handler \
        --zip-file fileb://deployment-package.zip \
        --timeout $TIMEOUT \
        --memory-size $MEMORY \
        --environment "Variables={OPENAI_API_KEY=$OPENAI_API_KEY,DYNAMODB_TABLE=$TABLE_NAME}" \
        --region $REGION > /dev/null
    
    # Wait for function to be active
    aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION
    
    echo -e "${GREEN}✓${NC} Function created"
fi

# ==============================================================================
# Step 5: Create API Gateway
# ==============================================================================
echo ""
echo -e "${YELLOW}Step 5: Setting up API Gateway...${NC}"

API_NAME="${FUNCTION_NAME}-api"

# Check if API exists
EXISTING_API=$(aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='$API_NAME'].ApiId" --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_API" ] && [ "$EXISTING_API" != "None" ]; then
    API_ID=$EXISTING_API
    echo -e "${GREEN}✓${NC} API Gateway already exists: $API_ID"
else
    # Create HTTP API
    API_RESPONSE=$(aws apigatewayv2 create-api \
        --name $API_NAME \
        --protocol-type HTTP \
        --target "arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME" \
        --region $REGION)
    
    API_ID=$(echo $API_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['ApiId'])")
    
    # Add Lambda permission for API Gateway
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id apigateway-invoke \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*" \
        --region $REGION 2>/dev/null || true
    
    echo -e "${GREEN}✓${NC} API Gateway created: $API_ID"
fi

# Get API endpoint
API_ENDPOINT=$(aws apigatewayv2 get-api --api-id $API_ID --region $REGION --query 'ApiEndpoint' --output text)

# ==============================================================================
# Done!
# ==============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Your AI agent is now live at:"
echo -e "${GREEN}$API_ENDPOINT${NC}"
echo ""
echo "Test it with:"
echo -e "${YELLOW}curl -X POST $API_ENDPOINT \\
  -H 'Content-Type: application/json' \\
  -d '{\"message\": \"What are your store hours?\"}'${NC}"
echo ""
echo "Resources created:"
echo "  • Lambda Function: $FUNCTION_NAME"
echo "  • DynamoDB Table:  $TABLE_NAME"
echo "  • API Gateway:     $API_NAME"
echo "  • IAM Role:        $ROLE_NAME"
echo ""

# Save endpoint to file for reference
echo "$API_ENDPOINT" > .api-endpoint
echo -e "API endpoint saved to ${GREEN}.api-endpoint${NC}"

# Cleanup
rm -f deployment-package.zip

