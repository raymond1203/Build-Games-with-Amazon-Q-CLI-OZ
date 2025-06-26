# AWS Problem Solver Game - API Documentation

## Base URL
```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

## Authentication
현재 버전에서는 인증이 필요하지 않습니다. 향후 JWT 토큰 기반 인증을 추가할 예정입니다.

## Common Headers
```
Content-Type: application/json
Access-Control-Allow-Origin: *
```

## Error Response Format
```json
{
  "error": "Error message",
  "details": "Detailed error information (optional)",
  "timestamp": "2025-06-26T10:00:00Z"
}
```

---

## Questions API

### GET /questions/random
랜덤 문제 조회

**Query Parameters:**
- `category` (optional): 문제 카테고리 (EC2, S3, RDS, VPC, LAMBDA)
- `difficulty` (optional): 난이도 (easy, medium, hard)
- `npc` (optional): NPC ID (alex_ceo, sarah_analyst, mike_security, jenny_developer)

**Response:**
```json
{
  "question": {
    "questionId": "ec2_001",
    "category": "EC2",
    "difficulty": "medium",
    "npcCharacter": "alex_ceo",
    "scenario": {
      "title": "웹사이트 트래픽 급증",
      "description": "스타트업 CEO Alex가 찾아왔습니다...",
      "context": "현재 단일 EC2 인스턴스에서..."
    },
    "question": "이 상황을 해결하기 위한 가장 적절한 AWS 솔루션은?",
    "options": [
      {"id": "A", "text": "더 큰 EC2 인스턴스로 업그레이드"},
      {"id": "B", "text": "Application Load Balancer와 Auto Scaling Group 구성"},
      {"id": "C", "text": "CloudFront CDN만 추가"},
      {"id": "D", "text": "RDS 읽기 전용 복제본 추가"}
    ],
    "tags": ["auto-scaling", "load-balancer"],
    "estimatedTime": 60,
    "points": 100
  },
  "selection_method": "random",
  "filters_applied": {
    "category": "EC2",
    "difficulty": "medium"
  }
}
```

### GET /questions/adaptive
사용자 맞춤형 문제 조회

**Query Parameters:**
- `userId` (required): 사용자 ID
- `npcId` (optional): NPC ID
- `scenarioId` (optional): 시나리오 ID

**Response:**
```json
{
  "question": {
    // 문제 데이터 (위와 동일)
  },
  "adaptive_info": {
    "user_id": "user_12345",
    "selection_method": "adaptive",
    "context": {
      "npc_id": "alex_ceo",
      "scenario_id": "startup_scaling"
    }
  }
}
```

### GET /questions/npc
NPC별 맞춤 문제 조회

**Query Parameters:**
- `npcId` (required): NPC ID
- `count` (optional): 문제 개수 (기본값: 5)
- `userLevel` (optional): 사용자 레벨 (기본값: 1)

**Response:**
```json
{
  "questions": [
    {
      // 문제 데이터 배열
    }
  ],
  "npc_id": "alex_ceo",
  "count": 5,
  "user_level": 3
}
```

### GET /questions/scenario
시나리오별 문제 조회

**Query Parameters:**
- `scenarioId` (required): 시나리오 ID
- `phase` (optional): 시나리오 단계 (기본값: 1)

**Response:**
```json
{
  "questions": [
    {
      // 문제 데이터 배열
    }
  ],
  "scenario_id": "startup_scaling",
  "phase": 1,
  "count": 3
}
```

---

## Answer API

### POST /answer
답안 제출 및 검증

**Request Body:**
```json
{
  "action": "validate_answer",
  "questionId": "ec2_001",
  "selectedAnswer": "B",
  "userId": "user_12345",
  "timeSpent": 45,
  "hintsUsed": 1
}
```

**Response:**
```json
{
  "questionId": "ec2_001",
  "selectedAnswer": "B",
  "correctAnswer": "B",
  "isCorrect": true,
  "explanation": "트래픽 급증에 대응하려면 수평적 확장이 필요합니다...",
  "score": {
    "points": 90,
    "experience": 65,
    "bonus": 10,
    "breakdown": {
      "base": 100,
      "difficulty": 50,
      "time": 10,
      "hint_penalty": -10
    }
  },
  "timeSpent": 45,
  "hintsUsed": 1,
  "difficulty": "medium",
  "category": "EC2",
  "tags": ["auto-scaling", "load-balancer"],
  "learning_resources": [
    {
      "type": "documentation",
      "title": "AWS EC2 Auto Scaling 가이드",
      "url": "https://docs.aws.amazon.com/autoscaling/"
    }
  ]
}
```

---

## Hints API

### POST /hints
힌트 요청

**Request Body:**
```json
{
  "action": "get_hint",
  "userId": "user_12345",
  "questionId": "ec2_001",
  "hintLevel": 1
}
```

**Response:**
```json
{
  "hint": "트래픽이 급증할 때는 서버를 더 크게 만드는 것보다 서버 개수를 늘리는 것이 효과적입니다.",
  "hintLevel": 1,
  "maxHints": 3,
  "pointsPenalty": 10,
  "source": "predefined",
  "timestamp": "2025-06-26T10:00:00Z"
}
```

### POST /hints (NPC 힌트)
NPC 캐릭터를 통한 힌트 요청

**Request Body:**
```json
{
  "action": "get_npc_hint",
  "sessionId": "session_20250626_001",
  "questionData": {
    "questionId": "ec2_001",
    "category": "EC2",
    "difficulty": "medium"
  },
  "hintLevel": 1
}
```

**Response:**
```json
{
  "session_id": "session_20250626_001",
  "message": "Alex: 시간이 없어요! 트래픽 분산을 고려해보세요. 빨리 해결해봅시다!",
  "hint": "트래픽 분산을 고려해보세요",
  "hint_level": 1,
  "type": "npc_hint",
  "personality_style": "urgent",
  "timestamp": "2025-06-26T10:00:00Z"
}
```

### POST /hints (힌트 사용 검증)
힌트 사용 권한 검증

**Request Body:**
```json
{
  "action": "validate_hint_usage",
  "userId": "user_12345",
  "questionId": "ec2_001",
  "hintLevel": 1
}
```

**Response:**
```json
{
  "can_use_hint": true,
  "hint_level": 1,
  "points_penalty": 10,
  "remaining_daily_hints": 15,
  "remaining_question_hints": 2
}
```

---

## Leaderboard API

### GET /leaderboard
리더보드 조회

**Query Parameters:**
- `type` (optional): 리더보드 타입 (daily, weekly, monthly, alltime) - 기본값: alltime
- `limit` (optional): 조회할 순위 수 (기본값: 10)

**Response:**
```json
{
  "leaderboard": [
    {
      "leaderboardType": "alltime",
      "score": 2500,
      "userId": "user_12345",
      "username": "게임마스터",
      "rank": 1,
      "level": 5,
      "accuracy": 85.5,
      "updatedAt": "2025-06-26T10:00:00Z",
      "position": 1
    }
  ],
  "type": "alltime",
  "count": 10,
  "lastUpdated": "2025-06-26T10:00:00Z"
}
```

### GET /user-rank
특정 사용자 순위 조회

**Query Parameters:**
- `userId` (required): 사용자 ID
- `type` (optional): 리더보드 타입 (기본값: alltime)

**Response:**
```json
{
  "user_id": "user_12345",
  "leaderboard_type": "alltime",
  "rank": 15,
  "score": 1850,
  "total_participants": 150,
  "percentile": 90.0,
  "user_info": {
    "username": "게임마스터",
    "level": 4,
    "accuracy": 78.5
  }
}
```

### GET /leaderboard/stats
리더보드 통계 조회

**Query Parameters:**
- `type` (optional): 리더보드 타입 (기본값: alltime)

**Response:**
```json
{
  "leaderboard_type": "alltime",
  "statistics": {
    "total_participants": 150,
    "average_score": 1250.5,
    "highest_score": 5000,
    "lowest_score": 100,
    "average_level": 3.2,
    "average_accuracy": 68.5,
    "score_distribution": {
      "0-999": 45,
      "1000-2499": 60,
      "2500-4999": 35,
      "5000-9999": 8,
      "10000+": 2
    },
    "level_distribution": {
      "1-3": 80,
      "4-6": 45,
      "7-9": 20,
      "10-12": 4,
      "13+": 1
    },
    "top_performers": [
      {
        "userId": "user_001",
        "username": "TopPlayer",
        "score": 5000,
        "level": 12
      }
    ]
  },
  "last_updated": "2025-06-26T10:00:00Z"
}
```

### POST /leaderboard
리더보드 업데이트

**Request Body:**
```json
{
  "action": "update_leaderboard",
  "userId": "user_12345"
}
```

**Response:**
```json
{
  "message": "리더보드가 성공적으로 업데이트되었습니다.",
  "userId": "user_12345"
}
```

---

## Score & Performance API

### POST /answer (성과 분석)
적응형 피드백 요청

**Request Body:**
```json
{
  "action": "get_adaptive_feedback",
  "userId": "user_12345",
  "questionResult": {
    "is_correct": true,
    "difficulty": "medium",
    "category": "EC2",
    "time_spent": 45,
    "hints_used": 1
  }
}
```

**Response:**
```json
{
  "feedback": {
    "feedback_type": "correct",
    "main_message": "완벽합니다! 힌트를 최소한으로 사용하면서 정답을 맞히셨네요!",
    "motivational_message": "이런 식으로 계속하시면 고급 레벨로 빠르게 성장할 수 있을 거예요!",
    "performance_evaluation": {
      "skill_assessment": "intermediate",
      "improvement_rate": "good",
      "consistency": "high"
    },
    "next_steps": [
      "더 어려운 난이도의 문제에 도전해보세요",
      "다른 AWS 서비스 카테고리도 학습해보세요"
    ],
    "difficulty_adjustment": "increase",
    "learning_tips": [
      "실제 AWS 콘솔에서 실습해보세요",
      "AWS 공식 문서를 참고하세요"
    ]
  },
  "user_id": "user_12345",
  "timestamp": "2025-06-26T10:00:00Z"
}
```

### GET /performance/{userId}
사용자 성과 분석 조회

**Path Parameters:**
- `userId`: 사용자 ID

**Query Parameters:**
- `days` (optional): 분석 기간 (일) - 기본값: 7

**Response:**
```json
{
  "user_id": "user_12345",
  "analysis_period_days": 7,
  "performance_analysis": {
    "basic_stats": {
      "total_questions": 25,
      "correct_answers": 18,
      "accuracy": 72.0,
      "average_time": 52.3,
      "time_efficiency": 0.78
    },
    "difficulty_performance": {
      "easy": {"accuracy": 90.0, "attempts": 10, "trend": "stable"},
      "medium": {"accuracy": 66.7, "attempts": 12, "trend": "improving"},
      "hard": {"accuracy": 33.3, "attempts": 3, "trend": "insufficient_data"}
    },
    "category_performance": {
      "EC2": {"accuracy": 80.0, "attempts": 10, "strength_level": "strong"},
      "S3": {"accuracy": 70.0, "attempts": 10, "strength_level": "moderate"},
      "RDS": {"accuracy": 60.0, "attempts": 5, "strength_level": "weak"}
    },
    "learning_trend": {
      "trend": "improving",
      "slope": 0.15,
      "recent_performance": [0.6, 0.7, 0.75]
    },
    "skill_level": "intermediate",
    "confidence_score": 0.72,
    "improvement_areas": ["RDS 기본 개념", "hard 난이도 문제 해결"]
  },
  "difficulty_recommendation": {
    "recommended_difficulty": "medium",
    "confidence": 0.85,
    "reasoning": "현재 medium 난이도에서 안정적인 성과를 보이고 있습니다.",
    "expected_success_rate": 70.0
  },
  "recent_results_count": 25
}
```

---

## Status & Health Check

### GET /hint/status
힌트 시스템 상태 조회

**Response:**
```json
{
  "system_status": {
    "q_cli_available": true,
    "npc_engine_available": true,
    "overall_status": "healthy"
  },
  "statistics": {
    "total_hints_provided": 1250,
    "q_cli_success_rate": 0.95,
    "average_response_time": 1.2,
    "most_requested_categories": ["EC2", "S3", "Lambda"]
  },
  "timestamp": "2025-06-26T10:00:00Z"
}
```

---

## Rate Limits
- 일반 API: 100 requests/minute per IP
- 힌트 API: 20 requests/minute per user
- 리더보드 업데이트: 10 requests/minute per user

## Error Codes
- `400` - Bad Request: 잘못된 요청 파라미터
- `401` - Unauthorized: 인증 실패 (향후 구현)
- `403` - Forbidden: 권한 없음 (힌트 사용 제한 등)
- `404` - Not Found: 리소스를 찾을 수 없음
- `429` - Too Many Requests: 요청 한도 초과
- `500` - Internal Server Error: 서버 내부 오류

## SDK Examples

### JavaScript/Node.js
```javascript
const API_BASE_URL = 'https://your-api-id.execute-api.region.amazonaws.com/dev';

// 랜덤 문제 조회
async function getRandomQuestion(category = null, difficulty = null) {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (difficulty) params.append('difficulty', difficulty);
  
  const response = await fetch(`${API_BASE_URL}/questions/random?${params}`);
  return await response.json();
}

// 답안 제출
async function submitAnswer(questionId, selectedAnswer, userId, timeSpent = 0, hintsUsed = 0) {
  const response = await fetch(`${API_BASE_URL}/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      action: 'validate_answer',
      questionId,
      selectedAnswer,
      userId,
      timeSpent,
      hintsUsed
    })
  });
  return await response.json();
}
```

### Python
```python
import requests

API_BASE_URL = 'https://your-api-id.execute-api.region.amazonaws.com/dev'

def get_random_question(category=None, difficulty=None):
    params = {}
    if category:
        params['category'] = category
    if difficulty:
        params['difficulty'] = difficulty
    
    response = requests.get(f'{API_BASE_URL}/questions/random', params=params)
    return response.json()

def submit_answer(question_id, selected_answer, user_id, time_spent=0, hints_used=0):
    data = {
        'action': 'validate_answer',
        'questionId': question_id,
        'selectedAnswer': selected_answer,
        'userId': user_id,
        'timeSpent': time_spent,
        'hintsUsed': hints_used
    }
    
    response = requests.post(f'{API_BASE_URL}/answer', json=data)
    return response.json()
```
