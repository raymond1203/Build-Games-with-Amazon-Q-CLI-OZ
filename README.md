# 🎮 AWS Problem Solver Game

> **Amazon Q CLI를 활용한 인터랙티브 AWS 학습 게임**

AWS 서비스에 대한 실무 지식을 게임을 통해 재미있게 학습할 수 있는 웹 애플리케이션입니다. NPC와의 대화를 통해 실제 비즈니스 시나리오를 경험하고, Amazon Q CLI의 AI 힌트를 받아 문제를 해결할 수 있습니다.

## 🌟 주요 기능

### 🤖 AI 기반 힌트 시스템
- **Amazon Q CLI 통합**: 실시간 AI 기반 힌트 제공
- **NPC별 개성**: 4개 캐릭터의 고유한 힌트 스타일
- **단계별 힌트**: 3단계 난이도별 힌트 시스템
- **대체 시스템**: Amazon Q CLI 없이도 완전 동작

### 👥 NPC 인터랙션 시스템
- **Alex (스타트업 CEO)**: 비즈니스 중심의 빠른 솔루션 제안
- **Sarah (데이터 분석가)**: 체계적이고 분석적인 접근
- **Mike (보안 담당자)**: 보안과 규제 준수 중심
- **Jenny (풀스택 개발자)**: 개발자 친화적이고 혁신적인 방법

### 🎯 레벨 시스템 & 성취 배지
- **20레벨 시스템**: 경험치 기반 진행률 관리
- **AWS 전문가 등급**: 입문자 → 레전드 (8단계)
- **11개 성취 배지**: 다양한 조건별 배지 획득
- **실시간 통계**: 정답률, 연속 정답, 총 점수 추적

### 🏗️ AWS 조언자 시스템
- **서비스 설명**: 50+ AWS 서비스 상세 설명
- **FAQ 시스템**: 자주 묻는 질문과 답변
- **모범 사례**: AWS 아키텍처 모범 사례 가이드
- **문제 해결**: 일반적인 AWS 문제 해결 방법

### 📊 성능 모니터링
- **실시간 성능 추적**: 로딩 시간, API 응답, 메모리 사용량
- **자동 권장사항**: 성능 개선 제안
- **오류 추적**: 실시간 오류 모니터링 및 분석
- **성능 대시보드**: 종합적인 성능 지표 시각화

## 🏗️ 아키텍처

### 서버리스 아키텍처
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudFront    │────│   S3 (Static)    │    │   API Gateway   │
│   (CDN)         │    │   (Frontend)     │    │   (REST API)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────┐              │
                       │   DynamoDB      │              │
                       │   (Game Data)   │              │
                       └─────────────────┘              │
                                                         │
                                               ┌─────────────────┐
                                               │   Lambda        │
                                               │   (Hint Provider)│
                                               └─────────────────┘
                                                         │
                                               ┌─────────────────┐
                                               │   Amazon Q CLI  │
                                               │   (AI Hints)    │
                                               └─────────────────┘
```

### 기술 스택
- **Frontend**: Vanilla JavaScript, CSS3, HTML5
- **Backend**: AWS Lambda (Python 3.9)
- **Database**: Amazon DynamoDB
- **API**: Amazon API Gateway
- **CDN**: Amazon CloudFront
- **Storage**: Amazon S3
- **AI**: Amazon Q CLI
- **IaC**: AWS SAM (Serverless Application Model)

## 🚀 빠른 시작

### 필수 요구사항
- AWS CLI 설치 및 구성
- SAM CLI 설치
- Node.js 16+ (개발용)
- Python 3.9+ (Lambda 함수용)

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/aws-problem-solver-game.git
cd aws-problem-solver-game
```

### 2. 의존성 설치
```bash
# Lambda 함수 의존성
pip install -r src/lambda_functions/requirements.txt

# 개발 도구 (선택사항)
npm install -g http-server
```

### 3. 배포
```bash
# 개발 환경 배포
./deploy.sh dev

# 프로덕션 환경 배포
./deploy.sh prod
```

### 4. Amazon Q CLI 설정 (선택사항)
```bash
# Amazon Q CLI 설치
pip install amazon-q-cli

# 설정
q configure
```

## 📖 사용 방법

### 게임 플레이
1. **사용자 등록**: 닉네임 입력 및 게임 모드 선택
2. **NPC 선택**: 4명의 캐릭터 중 선택
3. **문제 해결**: 4지선다 문제 풀이
4. **힌트 활용**: 어려운 문제에서 AI 힌트 요청
5. **결과 확인**: 점수 및 해설 확인
6. **레벨업**: 경험치 획득 및 성취 배지 수집

### AWS 조언자 활용
1. **서비스 검색**: AWS 서비스명으로 검색
2. **FAQ 확인**: 자주 묻는 질문 탐색
3. **모범 사례**: 아키텍처 가이드 참고
4. **문제 해결**: 일반적인 문제 해결 방법 확인

## 🧪 테스트

### 단위 테스트
```bash
# Python 단위 테스트
python -m pytest tests/test_hint_provider.py -v

# 프론트엔드 테스트
open tests/test_frontend.html
```

### 통합 테스트
```bash
# Selenium 기반 E2E 테스트
export TEST_BASE_URL="https://your-cloudfront-url"
export TEST_API_URL="https://your-api-gateway-url/dev"
python tests/integration_test.py
```

### 성능 테스트
```bash
# 성능 대시보드 열기
open performance_dashboard.html
```

## 📊 모니터링

### 성능 메트릭
- **로딩 성능**: DOM Content Loaded, First Contentful Paint
- **API 성능**: 응답 시간, 오류율, 처리량
- **메모리 사용량**: JS Heap 사용률, 메모리 누수 감지
- **사용자 경험**: 상호작용 응답성, Long Task 추적

### 대시보드 접근
```
https://your-domain.com/performance_dashboard.html
```

## 🔧 개발 가이드

### 로컬 개발 환경
```bash
# 로컬 서버 실행
http-server src/frontend -p 8000

# SAM 로컬 API 실행
sam local start-api
```

### 새로운 NPC 추가
1. `src/frontend/npc_system.js`에 NPC 데이터 추가
2. `src/frontend/styles/game.css`에 스타일 추가
3. `src/lambda_functions/hint_provider.py`에 힌트 스타일 추가

### 새로운 문제 추가
1. `src/frontend/game.js`의 `generateMockQuestion()` 수정
2. 문제 카테고리별 힌트 템플릿 업데이트

## 📁 프로젝트 구조

```
aws-problem-solver-game/
├── src/
│   ├── frontend/                 # 프론트엔드 소스
│   │   ├── index.html           # 메인 HTML
│   │   ├── game.js              # 게임 로직
│   │   ├── npc_system.js        # NPC 시스템
│   │   ├── level_system.js      # 레벨 시스템
│   │   ├── aws_advisor.js       # AWS 조언자
│   │   ├── performance_monitor.js # 성능 모니터
│   │   └── styles/
│   │       └── game.css         # 스타일시트
│   └── lambda_functions/         # Lambda 함수
│       ├── hint_provider.py     # 힌트 제공자
│       └── requirements.txt     # Python 의존성
├── tests/                       # 테스트 파일
│   ├── test_hint_provider.py    # 단위 테스트
│   ├── test_frontend.html       # 프론트엔드 테스트
│   └── integration_test.py      # 통합 테스트
├── template.yaml               # SAM 템플릿
├── deploy.sh                   # 배포 스크립트
├── performance_dashboard.html  # 성능 대시보드
└── README.md                   # 이 파일
```

## 🔐 보안

### 구현된 보안 기능
- **CORS 설정**: API Gateway CORS 정책
- **IAM 역할**: 최소 권한 원칙 적용
- **HTTPS 강제**: CloudFront HTTPS 리다이렉트
- **입력 검증**: 클라이언트/서버 양쪽 검증
- **오류 처리**: 민감한 정보 노출 방지

### 보안 모범 사례
- API 키 환경 변수 관리
- 정기적인 의존성 업데이트
- CloudTrail 로깅 활성화
- WAF 규칙 적용 (프로덕션)

## 🚀 배포 환경

### 개발 환경 (dev)
- **목적**: 개발 및 테스트
- **도메인**: `dev-aws-game.your-domain.com`
- **모니터링**: 기본 CloudWatch

### 프로덕션 환경 (prod)
- **목적**: 실제 서비스
- **도메인**: `aws-game.your-domain.com`
- **모니터링**: 고급 CloudWatch + X-Ray
- **백업**: 자동 백업 활성화

## 📈 성능 최적화

### 구현된 최적화
- **코드 분할**: 모듈별 JavaScript 분리
- **이미지 최적화**: WebP 포맷 사용
- **캐싱 전략**: CloudFront 캐시 정책
- **압축**: Gzip/Brotli 압축 활성화
- **지연 로딩**: 필요시에만 리소스 로드

### 성능 목표
- **First Contentful Paint**: < 1.5초
- **Time to Interactive**: < 3초
- **API 응답 시간**: < 500ms
- **메모리 사용률**: < 80%

## 🤝 기여 방법

### 버그 리포트
1. GitHub Issues에서 기존 이슈 확인
2. 재현 가능한 단계 포함하여 이슈 생성
3. 환경 정보 (브라우저, OS 등) 포함

### 기능 제안
1. 기능 제안서 작성
2. 사용 사례 및 예상 효과 설명
3. 구현 방안 제시 (선택사항)

### 코드 기여
1. Fork 및 브랜치 생성
2. 코드 작성 및 테스트
3. Pull Request 생성

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🙏 감사의 말

- **AWS**: 클라우드 인프라 제공
- **Amazon Q**: AI 기반 힌트 시스템
- **오픈소스 커뮤니티**: 다양한 라이브러리 제공

## 📞 지원

### 문서
- [AWS 공식 문서](https://docs.aws.amazon.com/)
- [Amazon Q 개발자 가이드](https://docs.aws.amazon.com/amazonq/)
- [SAM 개발자 가이드](https://docs.aws.amazon.com/serverless-application-model/)

### 커뮤니티
- [GitHub Issues](https://github.com/your-username/aws-problem-solver-game/issues)
- [AWS 커뮤니티 포럼](https://forums.aws.amazon.com/)
- [Discord 서버](https://discord.gg/your-server)

---

**Made with ❤️ for AWS Learning Community**

> 이 프로젝트는 AWS 학습을 재미있게 만들기 위해 개발되었습니다. 
> 여러분의 AWS 여정에 도움이 되기를 바랍니다! 🚀
