#!/bin/bash

# AWS Problem Solver Game - API Deployment Script
# This script deploys the API Gateway and Lambda functions

set -e

# Configuration
STACK_NAME="aws-problem-solver-game-api"
ENVIRONMENT=${1:-dev}
REGION=${AWS_REGION:-us-east-1}
CORS_ORIGIN=${CORS_ORIGIN:-'*'}

echo "🚀 Starting deployment for AWS Problem Solver Game API"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack Name: $STACK_NAME-$ENVIRONMENT"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Create deployment package directory
DEPLOY_DIR="./deploy"
mkdir -p $DEPLOY_DIR

echo "📦 Preparing Lambda deployment packages..."

# Package Lambda functions
for function in question_manager score_calculator hint_provider leaderboard; do
    echo "Packaging $function..."
    
    # Create function directory
    FUNC_DIR="$DEPLOY_DIR/$function"
    mkdir -p $FUNC_DIR
    
    # Copy function code
    cp src/lambda_functions/${function}.py $FUNC_DIR/
    
    # Copy utility modules
    cp -r src/utils $FUNC_DIR/ 2>/dev/null || true
    cp -r src/game_data $FUNC_DIR/ 2>/dev/null || true
    
    # Create requirements.txt if it doesn't exist
    if [ ! -f $FUNC_DIR/requirements.txt ]; then
        cat > $FUNC_DIR/requirements.txt << EOF
boto3>=1.26.0
botocore>=1.29.0
EOF
    fi
    
    # Install dependencies
    if [ -f $FUNC_DIR/requirements.txt ]; then
        pip install -r $FUNC_DIR/requirements.txt -t $FUNC_DIR/ --quiet
    fi
    
    # Create ZIP package
    cd $FUNC_DIR
    zip -r ../${function}.zip . -q
    cd - > /dev/null
    
    echo "✅ $function packaged successfully"
done

echo "☁️  Deploying CloudFormation stack..."

# Deploy DynamoDB tables first (if not exists)
echo "Checking DynamoDB tables..."
if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME-db-$ENVIRONMENT" --region $REGION > /dev/null 2>&1; then
    echo "Deploying DynamoDB tables..."
    aws cloudformation deploy \
        --template-file infrastructure/cloudformation/dynamodb-tables.yaml \
        --stack-name "$STACK_NAME-db-$ENVIRONMENT" \
        --region $REGION \
        --no-fail-on-empty-changeset
    
    echo "✅ DynamoDB tables deployed"
else
    echo "✅ DynamoDB tables already exist"
fi

# Deploy API Gateway and Lambda functions
echo "Deploying API Gateway and Lambda functions..."

# Upload Lambda packages to S3 (if S3 bucket exists)
S3_BUCKET="aws-problem-solver-game-deployments-$ENVIRONMENT"
if aws s3 ls "s3://$S3_BUCKET" > /dev/null 2>&1; then
    echo "Uploading Lambda packages to S3..."
    for function in question_manager score_calculator hint_provider leaderboard; do
        aws s3 cp $DEPLOY_DIR/${function}.zip s3://$S3_BUCKET/lambda/${function}.zip
    done
    
    # Use S3 deployment
    aws cloudformation deploy \
        --template-file infrastructure/cloudformation/api-gateway.yaml \
        --stack-name "$STACK_NAME-$ENVIRONMENT" \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            CorsOrigin="$CORS_ORIGIN" \
            S3Bucket=$S3_BUCKET \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION \
        --no-fail-on-empty-changeset
else
    echo "S3 bucket not found, using inline deployment..."
    
    # Update Lambda functions with local packages
    for function in question_manager score_calculator hint_provider leaderboard; do
        FUNCTION_NAME="game-$function-$ENVIRONMENT"
        
        # Check if function exists
        if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
            echo "Updating $FUNCTION_NAME..."
            aws lambda update-function-code \
                --function-name $FUNCTION_NAME \
                --zip-file fileb://$DEPLOY_DIR/${function}.zip \
                --region $REGION > /dev/null
        else
            echo "Function $FUNCTION_NAME not found, will be created by CloudFormation"
        fi
    done
    
    # Deploy CloudFormation stack
    aws cloudformation deploy \
        --template-file infrastructure/cloudformation/api-gateway.yaml \
        --stack-name "$STACK_NAME-$ENVIRONMENT" \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            CorsOrigin="$CORS_ORIGIN" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION \
        --no-fail-on-empty-changeset
fi

# Get API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 API Gateway URL: $API_URL"
echo ""
echo "📋 Available endpoints:"
echo "  GET  $API_URL/questions/random"
echo "  GET  $API_URL/questions/adaptive"
echo "  GET  $API_URL/questions/npc"
echo "  GET  $API_URL/questions/scenario"
echo "  POST $API_URL/answer"
echo "  POST $API_URL/hints"
echo "  GET  $API_URL/leaderboard"
echo "  POST $API_URL/leaderboard"
echo ""

# Test API endpoints
echo "🧪 Testing API endpoints..."

# Test random question endpoint
echo "Testing GET /questions/random..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/questions/random")
if [ "$RESPONSE" = "200" ]; then
    echo "✅ Random questions endpoint is working"
else
    echo "⚠️  Random questions endpoint returned status: $RESPONSE"
fi

# Test leaderboard endpoint
echo "Testing GET /leaderboard..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/leaderboard")
if [ "$RESPONSE" = "200" ]; then
    echo "✅ Leaderboard endpoint is working"
else
    echo "⚠️  Leaderboard endpoint returned status: $RESPONSE"
fi

echo ""
echo "🎉 Deployment and testing completed!"
echo ""
echo "📖 API Documentation: docs/api-documentation.md"
echo "🔧 To update Lambda code only: ./scripts/update-lambda.sh $ENVIRONMENT"
echo "🗑️  To delete the stack: aws cloudformation delete-stack --stack-name $STACK_NAME-$ENVIRONMENT --region $REGION"

# Cleanup
rm -rf $DEPLOY_DIR
echo "🧹 Cleanup completed"
