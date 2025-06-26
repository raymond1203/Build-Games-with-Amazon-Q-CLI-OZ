# 🔌 API Documentation

AWS Problem Solver Game의 REST API 문서입니다.

## Base URL

```
Production: https://your-api-gateway-id.execute-api.region.amazonaws.com/prod
Development: https://your-api-gateway-id.execute-api.region.amazonaws.com/dev
```

## Authentication

현재 버전에서는 인증이 필요하지 않습니다. 향후 버전에서 API 키 기반 인증이 추가될 예정입니다.

## Common Headers

```http
Content-Type: application/json
Accept: application/json
```

## Error Responses

모든 API 엔드포인트는 다음과 같은 형식의 오류 응답을 반환합니다:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

---

## 🎯 Hints API

### Get Hint

NPC로부터 문제 해결 힌트를 요청합니다.

**Endpoint:** `POST /hints`

**Request Body:**
```json
{
  "action": "get_hint",
  "sessionId": "session_12345",
  "questionData": {
    "questionId": "q001",
    "category": "EC2",
    "difficulty": "medium",
    "scenario": {
      "title": "웹 애플리케이션 확장성 문제",
      "description": "트래픽이 급증하여 단일 EC2 인스턴스의 CPU 사용률이 90%를 넘고 있습니다.",
      "context": "현재 단일 EC2 인스턴스에서 실행 중이며, 피크 시간대에 응답 시간이 느려지고 있습니다."
    },
    "question": "이 상황에서 가장 적절한 AWS 솔루션은 무엇입니까?"
  },
  "npcId": "alex_ceo",
  "hintLevel": 1
}
```

**Response:**
```json
{
  "hint": "Auto Scaling Group과 Load Balancer를 고려해보세요.",
  "message": "빠르게 해결해야 해요! Auto Scaling Group과 Load Balancer를 고려해보세요. 시간이 중요해요!",
  "source": "amazon_q",
  "npcId": "alex_ceo",
  "hintLevel": 1,
  "context": {
    "category": "EC2",
    "difficulty": "medium",
    "scenario": "트래픽이 급증하여...",
    "question": "이 상황에서 가장 적절한..."
  },
  "success": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | 항상 "get_hint" |
| `sessionId` | string | No | 게임 세션 ID |
| `questionData` | object | Yes | 문제 정보 |
| `questionData.questionId` | string | Yes | 문제 고유 ID |
| `questionData.category` | string | Yes | AWS 서비스 카테고리 |
| `questionData.difficulty` | string | Yes | 난이도 (easy/medium/hard) |
| `questionData.scenario` | object | Yes | 시나리오 정보 |
| `questionData.question` | string | Yes | 문제 텍스트 |
| `npcId` | string | Yes | NPC ID (alex_ceo/sarah_analyst/mike_security/jenny_developer) |
| `hintLevel` | integer | Yes | 힌트 레벨 (1-3) |

---

### Get AWS Service Explanation

AWS 서비스에 대한 상세 설명을 요청합니다.

**Endpoint:** `POST /hints`

**Request Body:**
```json
{
  "action": "get_explanation",
  "serviceName": "EC2",
  "context": "웹 애플리케이션 호스팅을 위한 EC2 사용법"
}
```

**Response:**
```json
{
  "explanation": "**Amazon EC2 (Elastic Compute Cloud)**\n\n**개요**\nAmazon EC2는 클라우드에서 안전하고 크기 조정 가능한 컴퓨팅 파워를 제공하는 웹 서비스입니다.\n\n**주요 기능**\n• 다양한 인스턴스 타입\n• Auto Scaling\n• Elastic Load Balancing\n• EBS 스토리지\n\n**사용 사례**\n• 웹 애플리케이션 호스팅\n• 고성능 컴퓨팅\n• 개발 및 테스트 환경\n\n**모범 사례**\n• 적절한 인스턴스 타입 선택\n• 보안 그룹 설정\n• 정기적인 백업\n• Reserved Instance 활용",
  "service": "EC2",
  "source": "amazon_q",
  "success": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | 항상 "get_explanation" |
| `serviceName` | string | Yes | AWS 서비스명 |
| `context` | string | No | 추가 컨텍스트 정보 |

---

## 📊 Game Data API (Future)

> 향후 버전에서 구현 예정인 API들입니다.

### Save Game Progress

**Endpoint:** `POST /game/progress`

**Request Body:**
```json
{
  "userId": "user_12345",
  "sessionId": "session_67890",
  "progress": {
    "level": 5,
    "experience": 1250,
    "totalScore": 8500,
    "questionsAnswered": 45,
    "correctAnswers": 38,
    "achievements": ["first_correct", "streak_5", "ec2_expert"],
    "currentStreak": 3,
    "maxStreak": 8
  }
}
```

### Get Leaderboard

**Endpoint:** `GET /game/leaderboard`

**Query Parameters:**
- `type`: `daily` | `weekly` | `monthly` | `all-time`
- `limit`: number (default: 10, max: 100)

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "username": "AWSMaster",
      "score": 15000,
      "level": 12,
      "accuracy": 92.5,
      "achievements": 8
    }
  ],
  "type": "weekly",
  "totalPlayers": 1250,
  "lastUpdated": "2024-01-01T12:00:00Z"
}
```

### Get User Statistics

**Endpoint:** `GET /game/stats/{userId}`

**Response:**
```json
{
  "userId": "user_12345",
  "username": "PlayerName",
  "level": 5,
  "experience": 1250,
  "totalScore": 8500,
  "questionsAnswered": 45,
  "correctAnswers": 38,
  "accuracy": 84.4,
  "achievements": ["first_correct", "streak_5", "ec2_expert"],
  "currentStreak": 3,
  "maxStreak": 8,
  "categoryStats": {
    "EC2": { "answered": 12, "correct": 10 },
    "S3": { "answered": 8, "correct": 7 },
    "Lambda": { "answered": 6, "correct": 5 }
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "lastPlayed": "2024-01-15T14:30:00Z"
}
```

---

## 🔍 Error Handling

### Common Error Scenarios

#### Invalid Action
```json
{
  "error": "Invalid action",
  "message": "Action 'invalid_action' is not supported",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Missing Required Fields
```json
{
  "error": "Validation error",
  "message": "Missing required field: questionData",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Amazon Q CLI Error
```json
{
  "hint": "AWS의 관리형 서비스를 고려해보세요.",
  "message": "빠르게 해결해야 해요! AWS의 관리형 서비스를 고려해보세요. 시간이 중요해요!",
  "source": "fallback",
  "npcId": "alex_ceo",
  "hintLevel": 1,
  "success": true,
  "note": "Amazon Q CLI unavailable, using fallback system"
}
```

#### Rate Limiting (Future)
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again in 60 seconds.",
  "retryAfter": 60,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 📝 Request/Response Examples

### Complete Hint Request Flow

1. **Initial Hint Request (Level 1)**
```bash
curl -X POST https://api.aws-game.com/dev/hints \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_hint",
    "questionData": {
      "questionId": "q001",
      "category": "EC2",
      "difficulty": "medium",
      "scenario": {
        "description": "웹 애플리케이션 트래픽 급증"
      },
      "question": "확장성 문제 해결 방법은?"
    },
    "npcId": "alex_ceo",
    "hintLevel": 1
  }'
```

2. **Follow-up Hint Request (Level 2)**
```bash
curl -X POST https://api.aws-game.com/dev/hints \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_hint",
    "questionData": {
      "questionId": "q001",
      "category": "EC2",
      "difficulty": "medium",
      "scenario": {
        "description": "웹 애플리케이션 트래픽 급증"
      },
      "question": "확장성 문제 해결 방법은?"
    },
    "npcId": "alex_ceo",
    "hintLevel": 2
  }'
```

### Service Explanation Request

```bash
curl -X POST https://api.aws-game.com/dev/hints \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_explanation",
    "serviceName": "Lambda",
    "context": "서버리스 아키텍처 구현"
  }'
```

---

## 🧪 Testing the API

### Using curl

```bash
# Test hint endpoint
curl -X POST https://your-api-url/dev/hints \
  -H "Content-Type: application/json" \
  -d @test_hint_request.json

# Test explanation endpoint  
curl -X POST https://your-api-url/dev/hints \
  -H "Content-Type: application/json" \
  -d @test_explanation_request.json
```

### Using JavaScript (Frontend)

```javascript
// Hint request
const hintResponse = await fetch('/api/hints', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    action: 'get_hint',
    questionData: questionData,
    npcId: 'alex_ceo',
    hintLevel: 1
  })
});

const hintData = await hintResponse.json();
```

### Using Python

```python
import requests

# Hint request
response = requests.post(
    'https://your-api-url/dev/hints',
    json={
        'action': 'get_hint',
        'questionData': question_data,
        'npcId': 'alex_ceo',
        'hintLevel': 1
    }
)

hint_data = response.json()
```

---

## 📊 API Metrics & Monitoring

### CloudWatch Metrics

- **Invocations**: Lambda 함수 호출 수
- **Duration**: 평균 응답 시간
- **Errors**: 오류 발생 수
- **Throttles**: 제한된 요청 수

### Custom Metrics

- **Hint Requests by NPC**: NPC별 힌트 요청 통계
- **Question Categories**: 카테고리별 문제 요청 통계
- **Amazon Q CLI Usage**: AI 힌트 vs 대체 힌트 비율
- **Response Times**: 엔드포인트별 응답 시간

### Alarms

- **High Error Rate**: 오류율 5% 초과 시 알림
- **High Latency**: 응답 시간 3초 초과 시 알림
- **Low Success Rate**: 성공률 95% 미만 시 알림

---

## 🔄 API Versioning

현재 버전: `v1`

향후 버전 계획:
- `v1.1`: 사용자 인증 추가
- `v1.2`: 게임 데이터 저장 API
- `v2.0`: GraphQL 지원

---

## 📞 Support

API 관련 문의사항:
- GitHub Issues: [링크]
- 이메일: api-support@aws-game.com
- Discord: #api-support 채널

---

**Last Updated:** 2024-01-01  
**API Version:** v1.0  
**Documentation Version:** 1.0
