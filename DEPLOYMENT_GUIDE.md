# 🚀 배포 가이드

AWS Problem Solver Game을 실제 AWS 환경에 배포하는 완전한 가이드입니다.

## 📋 배포 전 준비사항

### 1. 필수 도구 설치

#### AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# https://aws.amazon.com/cli/ 에서 다운로드
```

#### SAM CLI
```bash
# macOS
brew install aws-sam-cli

# Linux
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install

# Windows
# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install-windows.html
```

#### jq (JSON 파싱용)
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq  # Ubuntu/Debian
sudo yum install jq      # CentOS/RHEL

# Windows
# https://stedolan.github.io/jq/download/
```

### 2. AWS 자격 증명 설정

```bash
# AWS 자격 증명 구성
aws configure

# 입력 정보:
# AWS Access Key ID: [YOUR_ACCESS_KEY]
# AWS Secret Access Key: [YOUR_SECRET_KEY]
# Default region name: us-east-1 (또는 원하는 리전)
# Default output format: json
```

### 3. 환경 변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 원하는 에디터 사용
```

## ⚙️ 환경 변수 설정

`.env` 파일에서 다음 값들을 **반드시 설정**해야 합니다:

### 🔧 필수 설정

```bash
# AWS 기본 설정
AWS_REGION=us-east-1                    # 배포할 AWS 리전
AWS_PROFILE=default                     # 사용할 AWS 프로필

# 프로젝트 설정
PROJECT_NAME=aws-problem-solver-game    # 프로젝트 이름 (리소스 명명에 사용)
ENVIRONMENT=dev                         # 배포 환경 (dev 또는 prod)
```

### 🌐 선택적 설정

```bash
# 커스텀 도메인 (선택사항)
CUSTOM_DOMAIN=                          # 예: aws-game.yourdomain.com
DEV_SUBDOMAIN=dev-aws-game             # 개발 환경 서브도메인

# 보안 설정
CORS_ORIGINS=*                         # CORS 허용 도메인 (프로덕션에서는 구체적으로 설정)

# 모니터링 설정
ENHANCED_MONITORING=false              # 고급 모니터링 (추가 비용 발생)
XRAY_TRACING=false                     # X-Ray 추적 (추가 비용 발생)

# Amazon Q CLI
AMAZON_Q_ENABLED=false                 # Amazon Q CLI 사용 여부

# 알림 설정 (선택사항)
NOTIFICATION_EMAIL=                    # 배포 알림 이메일
SLACK_WEBHOOK_URL=                     # Slack 알림 웹훅
```

## 🚀 배포 실행

### 1. 개발 환경 배포

```bash
# 개발 환경에 배포
./deploy.sh dev

# 또는 환경변수 파일의 ENVIRONMENT 값 사용
./deploy.sh
```

### 2. 프로덕션 환경 배포

```bash
# 프로덕션 환경에 배포
./deploy.sh prod
```

### 3. 배포 과정

배포 스크립트는 다음 단계를 자동으로 수행합니다:

1. **환경 변수 로드** - `.env` 파일에서 설정 읽기
2. **필수 도구 확인** - AWS CLI, SAM CLI, jq 설치 확인
3. **Amazon Q CLI 확인** - 설치 여부 확인 (선택사항)
4. **SAM 빌드** - Lambda 함수 및 리소스 빌드
5. **SAM 배포** - CloudFormation 스택 배포
6. **출력 정보 수집** - API URL, S3 버킷명 등 수집
7. **프론트엔드 설정 업데이트** - 실제 API URL로 교체
8. **프론트엔드 배포** - S3에 정적 파일 업로드
9. **CloudFront 캐시 무효화** - CDN 캐시 갱신
10. **배포 테스트** - 엔드포인트 응답 확인
11. **배포 정보 저장** - JSON 파일로 배포 정보 저장

## 📊 배포 결과 확인

### 배포 완료 후 출력 정보

```
🎉 배포 완료!

=== 배포 정보 ===
Environment: dev
Stack Name: aws-problem-solver-game-dev
Region: us-east-1
Deployment Time: 2024-06-26T15:00:00Z

=== 🎮 게임 접속 URL ===
Game URL: https://d1234567890.cloudfront.net

=== 🔗 기타 URL ===
API URL: https://abcdef1234.execute-api.us-east-1.amazonaws.com/dev
CloudFront URL: https://d1234567890.cloudfront.net

=== 🧪 테스트 페이지 ===
NPC 시스템: https://d1234567890.cloudfront.net/test_npc_system.html
문제 시스템: https://d1234567890.cloudfront.net/test_question_system.html
레벨 시스템: https://d1234567890.cloudfront.net/test_level_system.html
Amazon Q 통합: https://d1234567890.cloudfront.net/test_amazon_q_integration.html
성능 대시보드: https://d1234567890.cloudfront.net/performance_dashboard.html
```

### 배포 정보 파일

배포 완료 후 `deployment-info-{environment}.json` 파일이 생성됩니다:

```json
{
  "environment": "dev",
  "stackName": "aws-problem-solver-game-dev",
  "region": "us-east-1",
  "deploymentTime": "2024-06-26T15:00:00Z",
  "urls": {
    "gameUrl": "https://d1234567890.cloudfront.net",
    "apiUrl": "https://abcdef1234.execute-api.us-east-1.amazonaws.com/dev",
    "cdnUrl": "https://d1234567890.cloudfront.net"
  },
  "resources": {
    "bucketName": "aws-problem-solver-game-assets-dev-123456789012",
    "distributionId": "E1234567890ABC"
  },
  "features": {
    "amazonQEnabled": false,
    "enhancedMonitoring": false,
    "xrayTracing": false
  }
}
```

## 🧪 배포 후 테스트

### 1. 기본 기능 테스트

```bash
# 게임 URL 접속 테스트
curl -I https://your-game-url.cloudfront.net

# API 엔드포인트 테스트
curl -X POST https://your-api-url.execute-api.region.amazonaws.com/dev/hints \
  -H "Content-Type: application/json" \
  -d '{"action":"get_hint","questionData":{"category":"EC2"},"npcId":"alex_ceo","hintLevel":1}'
```

### 2. 브라우저 테스트

1. **메인 게임**: `https://your-game-url`
2. **NPC 시스템**: `https://your-game-url/test_npc_system.html`
3. **문제 시스템**: `https://your-game-url/test_question_system.html`
4. **레벨 시스템**: `https://your-game-url/test_level_system.html`
5. **성능 대시보드**: `https://your-game-url/performance_dashboard.html`

## 🔧 Amazon Q CLI 설정 (선택사항)

### 1. Amazon Q CLI 설치

```bash
# pip를 통한 설치
pip install amazon-q-cli

# 또는 AWS CLI v2와 함께 설치
aws configure set plugins.cli_legacy_plugin_path /usr/local/aws-cli/v2/current/dist
```

### 2. Amazon Q CLI 구성

```bash
# Amazon Q CLI 설정
q configure

# 자격 증명 및 리전 설정
q configure set region us-east-1
```

### 3. 기능 활성화

```bash
# .env 파일에서 Amazon Q 활성화
AMAZON_Q_ENABLED=true

# 재배포
./deploy.sh
```

## 🌐 커스텀 도메인 설정 (선택사항)

### 1. Route 53에서 도메인 설정

```bash
# 호스팅 존 생성 (도메인이 Route 53에 없는 경우)
aws route53 create-hosted-zone \
  --name yourdomain.com \
  --caller-reference $(date +%s)
```

### 2. SSL 인증서 요청

```bash
# ACM에서 SSL 인증서 요청 (us-east-1 리전에서)
aws acm request-certificate \
  --domain-name aws-game.yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

### 3. 환경 변수 업데이트

```bash
# .env 파일 수정
CUSTOM_DOMAIN=aws-game.yourdomain.com

# 재배포
./deploy.sh
```

## 📊 모니터링 설정

### 1. CloudWatch 대시보드

배포 후 CloudWatch에서 다음 메트릭을 모니터링할 수 있습니다:

- **Lambda 함수**: 호출 수, 오류율, 지속 시간
- **API Gateway**: 요청 수, 지연 시간, 오류율
- **CloudFront**: 요청 수, 캐시 적중률
- **S3**: 요청 수, 데이터 전송량

### 2. 알람 설정

프로덕션 환경에서는 자동으로 다음 알람이 설정됩니다:

- **높은 오류율**: Lambda 함수 오류가 10개 이상
- **높은 지연 시간**: Lambda 함수 실행 시간이 5초 이상

### 3. 로그 확인

```bash
# Lambda 함수 로그 확인
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/aws-problem-solver-game"

# 최근 로그 스트림 확인
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/aws-problem-solver-game-hint-provider-dev" \
  --order-by LastEventTime \
  --descending
```

## 🔄 업데이트 및 재배포

### 코드 변경 후 재배포

```bash
# 코드 변경 후 재배포
./deploy.sh dev

# 프론트엔드만 업데이트 (빠른 배포)
aws s3 sync src/frontend/ s3://your-bucket-name/ --delete
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

### 환경 변수 변경 후 재배포

```bash
# .env 파일 수정 후
./deploy.sh dev
```

## 🗑️ 리소스 정리

### 전체 스택 삭제

```bash
# CloudFormation 스택 삭제
aws cloudformation delete-stack --stack-name aws-problem-solver-game-dev

# S3 버킷 내용 삭제 (버킷 삭제 전 필수)
aws s3 rm s3://your-bucket-name --recursive
```

### 개별 리소스 확인

```bash
# 생성된 리소스 목록 확인
aws cloudformation list-stack-resources --stack-name aws-problem-solver-game-dev
```

## 💰 비용 최적화

### 개발 환경 비용 절약

1. **사용하지 않을 때 스택 삭제**
2. **Enhanced Monitoring 비활성화**
3. **X-Ray Tracing 비활성화**
4. **CloudFront 캐시 TTL 단축**

### 프로덕션 환경 최적화

1. **Reserved Capacity 사용** (예측 가능한 트래픽)
2. **S3 Intelligent Tiering** 활성화
3. **CloudFront 압축** 활성화
4. **Lambda 메모리 최적화**

## 🚨 문제 해결

### 일반적인 문제들

#### 1. SAM 빌드 실패
```bash
# Python 의존성 문제
pip install -r src/lambda_functions/requirements.txt

# Docker 관련 문제
sam build --use-container
```

#### 2. 배포 권한 오류
```bash
# IAM 권한 확인
aws iam get-user
aws sts get-caller-identity

# 필요한 권한: CloudFormation, Lambda, API Gateway, S3, CloudFront, IAM
```

#### 3. CloudFront 캐시 문제
```bash
# 강제 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

#### 4. API Gateway CORS 오류
- `.env` 파일의 `CORS_ORIGINS` 설정 확인
- 브라우저 개발자 도구에서 네트워크 탭 확인

### 로그 확인 방법

```bash
# CloudFormation 이벤트 확인
aws cloudformation describe-stack-events --stack-name aws-problem-solver-game-dev

# Lambda 함수 로그 확인
aws logs tail /aws/lambda/aws-problem-solver-game-hint-provider-dev --follow
```

## 📞 지원

### 문제 발생 시

1. **GitHub Issues**: 기술적 문제 신고
2. **배포 로그**: `deployment-info-{env}.json` 파일 첨부
3. **CloudFormation 이벤트**: 스택 배포 오류 시 이벤트 로그 확인

### 유용한 명령어

```bash
# 배포 상태 확인
aws cloudformation describe-stacks --stack-name aws-problem-solver-game-dev

# 리소스 목록 확인
aws cloudformation list-stack-resources --stack-name aws-problem-solver-game-dev

# 비용 확인
aws ce get-cost-and-usage \
  --time-period Start=2024-06-01,End=2024-06-30 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

**배포 성공을 기원합니다! 🚀**

> 문제가 발생하면 이 가이드를 참조하거나 GitHub Issues에 문의해주세요.
