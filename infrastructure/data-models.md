# DynamoDB 데이터 모델 설계

## 1. Users 테이블 (aws-game-users)

### 기본 구조
```json
{
  "userId": "user_12345",
  "email": "user@example.com",
  "username": "게임마스터",
  "level": 1,
  "experience": 150,
  "totalScore": 2500,
  "rank": "Junior Solutions Architect",
  "stats": {
    "totalQuestions": 45,
    "correctAnswers": 32,
    "accuracy": 71.1,
    "averageTime": 45.2,
    "hintsUsed": 8,
    "streakRecord": 7
  },
  "achievements": [
    "first_correct",
    "streak_5",
    "ec2_expert"
  ],
  "preferences": {
    "difficulty": "medium",
    "categories": ["EC2", "S3", "Lambda"],
    "hintsEnabled": true
  },
  "createdAt": "2025-06-26T09:00:00Z",
  "lastLoginAt": "2025-06-26T09:00:00Z",
  "isActive": true
}
```

### 인덱스
- **Primary Key**: userId (String)
- **GSI**: email-index (email)

## 2. Questions 테이블 (aws-game-questions)

### 기본 구조
```json
{
  "questionId": "q_ec2_001",
  "category": "EC2",
  "difficulty": "medium",
  "npcCharacter": "alex_ceo",
  "scenario": {
    "title": "트래픽 급증으로 인한 서버 다운",
    "description": "스타트업 CEO Alex가 찾아왔습니다. 웹사이트 트래픽이 갑자기 10배 증가하면서 서버가 다운되었다고 합니다.",
    "context": "현재 단일 EC2 인스턴스에서 웹 애플리케이션을 운영 중이며, 평소 100명의 동시 사용자를 처리하던 시스템이 갑자기 1000명의 사용자 요청을 받게 되었습니다."
  },
  "question": "이 상황을 해결하기 위한 가장 적절한 AWS 솔루션은 무엇입니까?",
  "options": [
    {
      "id": "A",
      "text": "더 큰 EC2 인스턴스로 업그레이드 (Vertical Scaling)",
      "isCorrect": false
    },
    {
      "id": "B", 
      "text": "Application Load Balancer와 Auto Scaling Group 구성",
      "isCorrect": true
    },
    {
      "id": "C",
      "text": "CloudFront CDN만 추가",
      "isCorrect": false
    },
    {
      "id": "D",
      "text": "RDS 읽기 전용 복제본 추가",
      "isCorrect": false
    }
  ],
  "explanation": "트래픽 급증에 대응하려면 수평적 확장(Horizontal Scaling)이 필요합니다. Application Load Balancer로 트래픽을 분산하고, Auto Scaling Group으로 인스턴스를 자동으로 추가/제거하는 것이 가장 효과적인 솔루션입니다.",
  "hints": [
    "트래픽이 급증할 때는 서버를 더 크게 만드는 것보다 서버 개수를 늘리는 것이 효과적입니다.",
    "AWS에는 트래픽을 여러 서버로 분산시키는 서비스가 있습니다.",
    "Auto Scaling은 트래픽에 따라 자동으로 서버 개수를 조절해줍니다."
  ],
  "tags": ["auto-scaling", "load-balancer", "high-availability"],
  "estimatedTime": 60,
  "points": 100,
  "createdAt": "2025-06-26T09:00:00Z",
  "updatedAt": "2025-06-26T09:00:00Z",
  "isActive": true
}
```

### 인덱스
- **Primary Key**: questionId (String)
- **GSI**: category-difficulty-index (category, difficulty)

## 3. GameSessions 테이블 (aws-game-sessions)

### 기본 구조
```json
{
  "sessionId": "session_20250626_001",
  "userId": "user_12345",
  "npcCharacter": "alex_ceo",
  "status": "completed",
  "questions": [
    {
      "questionId": "q_ec2_001",
      "selectedAnswer": "B",
      "isCorrect": true,
      "timeSpent": 45,
      "hintsUsed": 1,
      "points": 100
    }
  ],
  "summary": {
    "totalQuestions": 5,
    "correctAnswers": 4,
    "totalPoints": 400,
    "accuracy": 80.0,
    "totalTime": 240,
    "hintsUsed": 2
  },
  "createdAt": "2025-06-26T09:00:00Z",
  "completedAt": "2025-06-26T09:04:00Z",
  "ttl": 1735200000
}
```

### 인덱스
- **Primary Key**: sessionId (String)
- **GSI**: userId-createdAt-index (userId, createdAt)

## 4. Leaderboard 테이블 (aws-game-leaderboard)

### 기본 구조
```json
{
  "leaderboardType": "daily",
  "score": 2500,
  "userId": "user_12345",
  "username": "게임마스터",
  "rank": 1,
  "level": 5,
  "accuracy": 85.5,
  "totalQuestions": 120,
  "achievements": ["ec2_expert", "s3_master"],
  "updatedAt": "2025-06-26T09:00:00Z"
}
```

### 리더보드 타입
- `daily`: 일일 순위
- `weekly`: 주간 순위  
- `monthly`: 월간 순위
- `alltime`: 전체 순위

### 인덱스
- **Primary Key**: leaderboardType (String), score (Number)
- **GSI**: userId-index (userId)

## 데이터 관계도

```
Users (1) ←→ (N) GameSessions
Users (1) ←→ (N) Leaderboard
Questions (1) ←→ (N) GameSessions.questions
```

## 용량 및 성능 고려사항

### 예상 데이터 크기
- **Users**: 1,000명 × 2KB = 2MB
- **Questions**: 500개 × 5KB = 2.5MB  
- **GameSessions**: 10,000세션 × 3KB = 30MB
- **Leaderboard**: 4,000엔트리 × 1KB = 4MB

### 읽기/쓰기 패턴
- **Users**: 읽기 중심 (90% 읽기, 10% 쓰기)
- **Questions**: 읽기 전용 (95% 읽기, 5% 쓰기)
- **GameSessions**: 쓰기 중심 (30% 읽기, 70% 쓰기)
- **Leaderboard**: 균형 (60% 읽기, 40% 쓰기)

### 최적화 전략
- Pay-per-request 모드로 시작 (트래픽 예측 어려움)
- TTL 설정으로 오래된 세션 데이터 자동 삭제
- GSI 활용으로 다양한 쿼리 패턴 지원
- DynamoDB Streams로 실시간 리더보드 업데이트
