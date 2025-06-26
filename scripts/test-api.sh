#!/bin/bash

# AWS Problem Solver Game - API Testing Script
# This script tests all API endpoints to ensure they're working correctly

set -e

# Configuration
ENVIRONMENT=${1:-dev}
API_URL=${2:-}
REGION=${AWS_REGION:-us-east-1}

echo "🧪 Testing AWS Problem Solver Game API"
echo "Environment: $ENVIRONMENT"

# Get API URL if not provided
if [ -z "$API_URL" ]; then
    STACK_NAME="aws-problem-solver-game-api-$ENVIRONMENT"
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$API_URL" ]; then
        echo "❌ Could not find API URL. Please provide it as second argument or ensure the stack is deployed."
        exit 1
    fi
fi

echo "API URL: $API_URL"
echo ""

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing $description... "
    
    if [ "$method" = "GET" ]; then
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")
    else
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$API_URL$endpoint")
    fi
    
    if [ "$RESPONSE" = "$expected_status" ]; then
        echo "✅ PASS (Status: $RESPONSE)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "❌ FAIL (Expected: $expected_status, Got: $RESPONSE)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Function to test an endpoint with response content
test_endpoint_with_content() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing $description... "
    
    if [ "$method" = "GET" ]; then
        RESPONSE=$(curl -s "$API_URL$endpoint")
    else
        RESPONSE=$(curl -s -X "$method" -H "Content-Type: application/json" -d "$data" "$API_URL$endpoint")
    fi
    
    # Check if response contains error
    if echo "$RESPONSE" | grep -q '"error"'; then
        echo "❌ FAIL (Error in response)"
        echo "   Response: $RESPONSE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    else
        echo "✅ PASS"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
}

echo "🔍 Starting API endpoint tests..."
echo ""

# Test Questions API
echo "📝 Testing Questions API:"
test_endpoint "GET" "/questions/random" "200" "Random question endpoint"
test_endpoint "GET" "/questions/random?category=EC2" "200" "Random question with category filter"
test_endpoint "GET" "/questions/random?difficulty=easy" "200" "Random question with difficulty filter"
test_endpoint "GET" "/questions/adaptive?userId=test_user" "200" "Adaptive question endpoint"
test_endpoint "GET" "/questions/npc?npcId=alex_ceo" "200" "NPC questions endpoint"
test_endpoint "GET" "/questions/scenario?scenarioId=startup_scaling" "200" "Scenario questions endpoint"

echo ""

# Test Answer API
echo "📊 Testing Answer API:"
ANSWER_DATA='{"action":"validate_answer","questionId":"ec2_001","selectedAnswer":"B","userId":"test_user","timeSpent":45,"hintsUsed":0}'
test_endpoint "POST" "/answer" "200" "Answer validation endpoint" "$ANSWER_DATA"

echo ""

# Test Hints API
echo "💡 Testing Hints API:"
HINT_DATA='{"action":"get_hint","userId":"test_user","questionId":"ec2_001","hintLevel":1}'
test_endpoint "POST" "/hints" "200" "Basic hint request" "$HINT_DATA"

NPC_HINT_DATA='{"action":"get_npc_hint","sessionId":"test_session","questionData":{"questionId":"ec2_001","category":"EC2"},"hintLevel":1}'
test_endpoint "POST" "/hints" "200" "NPC hint request" "$NPC_HINT_DATA"

VALIDATE_HINT_DATA='{"action":"validate_hint_usage","userId":"test_user","questionId":"ec2_001","hintLevel":1}'
test_endpoint "POST" "/hints" "200" "Hint usage validation" "$VALIDATE_HINT_DATA"

echo ""

# Test Leaderboard API
echo "🏆 Testing Leaderboard API:"
test_endpoint "GET" "/leaderboard" "200" "Leaderboard endpoint"
test_endpoint "GET" "/leaderboard?type=daily&limit=5" "200" "Leaderboard with parameters"
test_endpoint "GET" "/user-rank?userId=test_user" "200" "User rank endpoint"
test_endpoint "GET" "/leaderboard/stats" "200" "Leaderboard statistics"

UPDATE_LEADERBOARD_DATA='{"action":"update_leaderboard","userId":"test_user"}'
test_endpoint "POST" "/leaderboard" "200" "Leaderboard update" "$UPDATE_LEADERBOARD_DATA"

echo ""

# Test CORS
echo "🌐 Testing CORS:"
test_endpoint "OPTIONS" "/questions/random" "200" "CORS preflight request"

echo ""

# Test Error Handling
echo "❌ Testing Error Handling:"
test_endpoint "GET" "/nonexistent" "404" "Non-existent endpoint"
test_endpoint "GET" "/questions/adaptive" "400" "Missing required parameter"

echo ""

# Test with actual content validation
echo "📋 Testing Response Content:"
test_endpoint_with_content "GET" "/questions/random" "Random question response content"
test_endpoint_with_content "GET" "/leaderboard?limit=1" "Leaderboard response content"

echo ""
echo "📊 Test Results Summary:"
echo "===================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! API is working correctly."
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Please check the API implementation."
    exit 1
fi
