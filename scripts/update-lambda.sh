#!/bin/bash

# AWS Problem Solver Game - Lambda Update Script
# This script updates only the Lambda function code without redeploying the entire stack

set -e

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${AWS_REGION:-us-east-1}
FUNCTION_PREFIX="game"

echo "🔄 Updating Lambda functions for environment: $ENVIRONMENT"
echo "Region: $REGION"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Create temporary deployment directory
DEPLOY_DIR="./deploy-lambda"
mkdir -p $DEPLOY_DIR

echo "📦 Preparing Lambda deployment packages..."

# Package and update each Lambda function
for function in question_manager score_calculator hint_provider leaderboard; do
    echo "Processing $function..."
    
    # Create function directory
    FUNC_DIR="$DEPLOY_DIR/$function"
    mkdir -p $FUNC_DIR
    
    # Copy function code
    cp src/lambda_functions/${function}.py $FUNC_DIR/
    
    # Copy utility modules
    if [ -d "src/utils" ]; then
        cp -r src/utils $FUNC_DIR/
    fi
    
    if [ -d "src/game_data" ]; then
        cp -r src/game_data $FUNC_DIR/
    fi
    
    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -t $FUNC_DIR/ --quiet
    fi
    
    # Create ZIP package
    cd $FUNC_DIR
    zip -r ../${function}.zip . -q
    cd - > /dev/null
    
    # Update Lambda function
    FUNCTION_NAME="$FUNCTION_PREFIX-$function-$ENVIRONMENT"
    
    echo "Updating $FUNCTION_NAME..."
    
    # Check if function exists
    if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
        # Update function code
        aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --zip-file fileb://$DEPLOY_DIR/${function}.zip \
            --region $REGION > /dev/null
        
        # Wait for update to complete
        aws lambda wait function-updated \
            --function-name $FUNCTION_NAME \
            --region $REGION
        
        echo "✅ $FUNCTION_NAME updated successfully"
    else
        echo "⚠️  Function $FUNCTION_NAME not found. Please deploy the full stack first."
    fi
done

echo ""
echo "🔄 Updating environment variables..."

# Update environment variables for each function
declare -A ENV_VARS
ENV_VARS[question_manager]="QUESTIONS_TABLE=aws-game-questions-$ENVIRONMENT,USERS_TABLE=aws-game-users-$ENVIRONMENT"
ENV_VARS[score_calculator]="USERS_TABLE=aws-game-users-$ENVIRONMENT,SESSIONS_TABLE=aws-game-sessions-$ENVIRONMENT,QUESTIONS_TABLE=aws-game-questions-$ENVIRONMENT,LEADERBOARD_TABLE=aws-game-leaderboard-$ENVIRONMENT"
ENV_VARS[hint_provider]="QUESTIONS_TABLE=aws-game-questions-$ENVIRONMENT,USERS_TABLE=aws-game-users-$ENVIRONMENT"
ENV_VARS[leaderboard]="LEADERBOARD_TABLE=aws-game-leaderboard-$ENVIRONMENT,USERS_TABLE=aws-game-users-$ENVIRONMENT"

for function in question_manager score_calculator hint_provider leaderboard; do
    FUNCTION_NAME="$FUNCTION_PREFIX-$function-$ENVIRONMENT"
    
    if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
        # Convert comma-separated env vars to JSON format
        ENV_JSON="{"
        IFS=',' read -ra VARS <<< "${ENV_VARS[$function]}"
        for i in "${!VARS[@]}"; do
            IFS='=' read -ra KV <<< "${VARS[i]}"
            ENV_JSON+="\"${KV[0]}\":\"${KV[1]}\""
            if [ $i -lt $((${#VARS[@]} - 1)) ]; then
                ENV_JSON+=","
            fi
        done
        ENV_JSON+="}"
        
        aws lambda update-function-configuration \
            --function-name $FUNCTION_NAME \
            --environment "Variables=$ENV_JSON" \
            --region $REGION > /dev/null
        
        echo "✅ Environment variables updated for $FUNCTION_NAME"
    fi
done

echo ""
echo "🧪 Testing updated functions..."

# Test each function with a simple invocation
for function in question_manager score_calculator hint_provider leaderboard; do
    FUNCTION_NAME="$FUNCTION_PREFIX-$function-$ENVIRONMENT"
    
    if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
        echo "Testing $FUNCTION_NAME..."
        
        # Create a simple test event
        TEST_EVENT='{"httpMethod":"OPTIONS","path":"/test"}'
        
        RESPONSE=$(aws lambda invoke \
            --function-name $FUNCTION_NAME \
            --payload "$TEST_EVENT" \
            --region $REGION \
            /tmp/lambda-response.json 2>&1)
        
        if echo "$RESPONSE" | grep -q "StatusCode.*200"; then
            echo "✅ $FUNCTION_NAME is responding correctly"
        else
            echo "⚠️  $FUNCTION_NAME test failed: $RESPONSE"
        fi
    fi
done

# Get API Gateway URL for testing
STACK_NAME="aws-problem-solver-game-api-$ENVIRONMENT"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$API_URL" ]; then
    echo ""
    echo "🌐 Testing API Gateway endpoints..."
    
    # Test a few key endpoints
    echo "Testing GET /questions/random..."
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/questions/random" || echo "000")
    if [ "$RESPONSE" = "200" ]; then
        echo "✅ API Gateway is working correctly"
    else
        echo "⚠️  API Gateway test returned status: $RESPONSE"
    fi
fi

# Cleanup
rm -rf $DEPLOY_DIR
rm -f /tmp/lambda-response.json

echo ""
echo "✅ Lambda functions updated successfully!"
echo ""
if [ -n "$API_URL" ]; then
    echo "🌐 API URL: $API_URL"
fi
echo "📖 API Documentation: docs/api-documentation.md"
echo "🔍 To view function logs: aws logs tail /aws/lambda/game-{function-name}-$ENVIRONMENT --follow"
