#!/bin/bash

# AWS Problem Solver Game - 배포 스크립트
# Amazon Q CLI 통합 및 서버리스 아키텍처 배포

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 변수 로드
load_environment() {
    if [ -f ".env" ]; then
        log_info ".env 파일에서 환경 변수 로드 중..."
        export $(grep -v '^#' .env | xargs)
    else
        log_warning ".env 파일이 없습니다. .env.example을 복사해서 설정하세요."
        log_info "cp .env.example .env"
        exit 1
    fi
}

# 환경 변수 설정
ENVIRONMENT=${1:-${ENVIRONMENT:-dev}}
PROJECT_NAME=${PROJECT_NAME:-aws-problem-solver-game}
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")

log_info "AWS Problem Solver Game 배포 시작"
log_info "Environment: ${ENVIRONMENT}"
log_info "Stack Name: ${STACK_NAME}"
log_info "Region: ${REGION}"
log_info "AWS Account: ${AWS_ACCOUNT_ID}"

# 필수 도구 확인
check_requirements() {
    log_info "필수 도구 확인 중..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI가 설치되지 않았습니다."
        exit 1
    fi
    
    if ! command -v sam &> /dev/null; then
        log_error "SAM CLI가 설치되지 않았습니다."
        log_info "설치 방법: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
        exit 1
    fi
    
    # AWS 자격 증명 확인
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS 자격 증명이 설정되지 않았습니다."
        log_info "aws configure를 실행하여 자격 증명을 설정하세요."
        exit 1
    fi
    
    log_success "모든 필수 도구가 설치되어 있습니다."
}

# Amazon Q CLI 확인
check_amazon_q() {
    log_info "Amazon Q CLI 확인 중..."
    
    if command -v q &> /dev/null; then
        Q_VERSION=$(q --version 2>/dev/null || echo "unknown")
        log_success "Amazon Q CLI 발견: ${Q_VERSION}"
        AMAZON_Q_ENABLED=true
    else
        log_warning "Amazon Q CLI가 설치되지 않았습니다."
        log_info "대체 힌트 시스템이 사용됩니다."
        log_info "Amazon Q CLI 설치: https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/cli-install.html"
        AMAZON_Q_ENABLED=false
    fi
}

# SAM 빌드
build_sam() {
    log_info "SAM 애플리케이션 빌드 중..."
    
    if sam build; then
        log_success "SAM 빌드 완료"
    else
        log_error "SAM 빌드 실패"
        exit 1
    fi
}

# SAM 배포
deploy_sam() {
    log_info "SAM 애플리케이션 배포 중..."
    
    # 배포 파라미터 구성
    DEPLOY_PARAMS="Environment=${ENVIRONMENT}"
    DEPLOY_PARAMS="${DEPLOY_PARAMS} ProjectName=${PROJECT_NAME}"
    
    if [ -n "${CUSTOM_DOMAIN}" ]; then
        DEPLOY_PARAMS="${DEPLOY_PARAMS} CustomDomain=${CUSTOM_DOMAIN}"
    fi
    
    if [ -n "${CORS_ORIGINS}" ]; then
        DEPLOY_PARAMS="${DEPLOY_PARAMS} CorsOrigins=${CORS_ORIGINS}"
    fi
    
    if [ "${ENHANCED_MONITORING}" = "true" ]; then
        DEPLOY_PARAMS="${DEPLOY_PARAMS} EnhancedMonitoring=true"
    fi
    
    if [ "${XRAY_TRACING}" = "true" ]; then
        DEPLOY_PARAMS="${DEPLOY_PARAMS} XRayTracing=true"
    fi
    
    if sam deploy \
        --stack-name "${STACK_NAME}" \
        --region "${REGION}" \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides ${DEPLOY_PARAMS} \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset; then
        log_success "SAM 배포 완료"
    else
        log_error "SAM 배포 실패"
        exit 1
    fi
}

# 스택 출력 가져오기
get_stack_outputs() {
    log_info "스택 출력 정보 가져오는 중..."
    
    OUTPUTS=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --region "${REGION}" \
        --query 'Stacks[0].Outputs' \
        --output json)
    
    API_URL=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="GameAPIUrl") | .OutputValue')
    BUCKET_NAME=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="GameAssetsBucketName") | .OutputValue')
    CDN_URL=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="GameCDNUrl") | .OutputValue')
    GAME_URL=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="GameURL") | .OutputValue')
    CDN_DISTRIBUTION_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="GameCDNDistributionId") | .OutputValue')
    
    log_success "스택 출력 정보:"
    echo "  API Gateway URL: ${API_URL}"
    echo "  S3 Bucket: ${BUCKET_NAME}"
    echo "  CloudFront URL: ${CDN_URL}"
    echo "  Game URL: ${GAME_URL}"
    echo "  Distribution ID: ${CDN_DISTRIBUTION_ID}"
}

# 프론트엔드 설정 업데이트
update_frontend_config() {
    log_info "프론트엔드 설정 업데이트 중..."
    
    # 임시 디렉토리 생성
    TEMP_DIR=$(mktemp -d)
    cp -r src/frontend/* "${TEMP_DIR}/"
    
    # index.html에서 API URL 교체
    sed -i.bak "s|API_GATEWAY_URL_PLACEHOLDER|${API_URL}|g" "${TEMP_DIR}/index.html"
    
    # Amazon Q 기능 활성화 설정
    if [ "${AMAZON_Q_ENABLED}" = "true" ]; then
        sed -i.bak "s|amazonQEnabled: false|amazonQEnabled: true|g" "${TEMP_DIR}/index.html"
    fi
    
    # 환경별 설정 적용
    if [ "${ENVIRONMENT}" = "prod" ]; then
        sed -i.bak "s|enhancedMonitoring: false|enhancedMonitoring: true|g" "${TEMP_DIR}/index.html"
    fi
    
    log_success "프론트엔드 설정 업데이트 완료"
    echo "  API URL: ${API_URL}"
    echo "  Amazon Q Enabled: ${AMAZON_Q_ENABLED}"
}

# 프론트엔드 배포
deploy_frontend() {
    log_info "프론트엔드 파일 S3에 업로드 중..."
    
    # S3에 파일 업로드
    if aws s3 sync "${TEMP_DIR}/" "s3://${BUCKET_NAME}/" \
        --region "${REGION}" \
        --delete \
        --cache-control "max-age=86400" \
        --exclude "*.bak"; then
        log_success "프론트엔드 배포 완료"
    else
        log_error "프론트엔드 배포 실패"
        exit 1
    fi
    
    # 임시 디렉토리 정리
    rm -rf "${TEMP_DIR}"
}

# CloudFront 캐시 무효화
invalidate_cloudfront() {
    log_info "CloudFront 캐시 무효화 중..."
    
    if [ -n "${CDN_DISTRIBUTION_ID}" ] && [ "${CDN_DISTRIBUTION_ID}" != "null" ]; then
        INVALIDATION_ID=$(aws cloudfront create-invalidation \
            --distribution-id "${CDN_DISTRIBUTION_ID}" \
            --paths "/*" \
            --region "${REGION}" \
            --query 'Invalidation.Id' \
            --output text)
        
        log_success "CloudFront 캐시 무효화 시작됨 (ID: ${INVALIDATION_ID})"
        log_info "무효화 완료까지 5-10분 소요될 수 있습니다."
    else
        log_warning "CloudFront 배포 ID를 찾을 수 없습니다."
    fi
}

# 배포 테스트
test_deployment() {
    log_info "배포 테스트 중..."
    
    # API 엔드포인트 테스트
    if curl -s -o /dev/null -w "%{http_code}" "${API_URL}/hints" | grep -q "405\|200"; then
        log_success "API 엔드포인트 응답 확인"
    else
        log_warning "API 엔드포인트 테스트 실패 (정상적일 수 있음)"
    fi
    
    # 게임 URL 테스트
    if curl -s -o /dev/null -w "%{http_code}" "${GAME_URL}" | grep -q "200"; then
        log_success "게임 URL 응답 확인"
    else
        log_warning "게임 URL 테스트 실패"
    fi
}

# 배포 정보 저장
save_deployment_info() {
    log_info "배포 정보 저장 중..."
    
    cat > "deployment-info-${ENVIRONMENT}.json" << EOF
{
  "environment": "${ENVIRONMENT}",
  "stackName": "${STACK_NAME}",
  "region": "${REGION}",
  "deploymentTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "urls": {
    "gameUrl": "${GAME_URL}",
    "apiUrl": "${API_URL}",
    "cdnUrl": "https://${CDN_URL}"
  },
  "resources": {
    "bucketName": "${BUCKET_NAME}",
    "distributionId": "${CDN_DISTRIBUTION_ID}"
  },
  "features": {
    "amazonQEnabled": ${AMAZON_Q_ENABLED},
    "enhancedMonitoring": "${ENHANCED_MONITORING:-false}",
    "xrayTracing": "${XRAY_TRACING:-false}"
  }
}
EOF
    
    log_success "배포 정보가 deployment-info-${ENVIRONMENT}.json에 저장되었습니다."
}

# 배포 정보 출력
print_deployment_info() {
    log_success "🎉 배포 완료!"
    echo ""
    echo "=== 배포 정보 ==="
    echo "Environment: ${ENVIRONMENT}"
    echo "Stack Name: ${STACK_NAME}"
    echo "Region: ${REGION}"
    echo "Deployment Time: $(date)"
    echo ""
    echo "=== 🎮 게임 접속 URL ==="
    echo "Game URL: ${GAME_URL}"
    echo ""
    echo "=== 🔗 기타 URL ==="
    echo "API URL: ${API_URL}"
    echo "CloudFront URL: https://${CDN_URL}"
    echo ""
    echo "=== 🧪 테스트 페이지 ==="
    echo "NPC 시스템: ${GAME_URL}/test_npc_system.html"
    echo "문제 시스템: ${GAME_URL}/test_question_system.html"
    echo "레벨 시스템: ${GAME_URL}/test_level_system.html"
    echo "Amazon Q 통합: ${GAME_URL}/test_amazon_q_integration.html"
    echo "성능 대시보드: ${GAME_URL}/performance_dashboard.html"
    echo ""
    echo "=== ⚙️ 기능 상태 ==="
    echo "Amazon Q CLI: $([ "${AMAZON_Q_ENABLED}" = "true" ] && echo "✅ 활성화" || echo "❌ 비활성화")"
    echo "Enhanced Monitoring: $([ "${ENHANCED_MONITORING}" = "true" ] && echo "✅ 활성화" || echo "❌ 비활성화")"
    echo "X-Ray Tracing: $([ "${XRAY_TRACING}" = "true" ] && echo "✅ 활성화" || echo "❌ 비활성화")"
    echo ""
    echo "=== 📋 다음 단계 ==="
    echo "1. 게임 URL에 접속하여 테스트"
    echo "2. Amazon Q CLI 설치 및 설정 (선택사항)"
    echo "3. 커스텀 도메인 설정 (선택사항)"
    echo "4. 모니터링 및 알람 설정 확인"
    echo ""
    echo "=== 📞 지원 ==="
    echo "문제 발생 시: GitHub Issues 또는 문서 참조"
    echo "배포 정보: deployment-info-${ENVIRONMENT}.json"
}

# 메인 실행 함수
main() {
    load_environment
    check_requirements
    check_amazon_q
    build_sam
    deploy_sam
    get_stack_outputs
    update_frontend_config
    deploy_frontend
    invalidate_cloudfront
    test_deployment
    save_deployment_info
    print_deployment_info
}

# 도움말 출력
show_help() {
    echo "AWS Problem Solver Game 배포 스크립트"
    echo ""
    echo "사용법:"
    echo "  ./deploy.sh [environment]"
    echo ""
    echo "매개변수:"
    echo "  environment    배포 환경 (dev 또는 prod, 기본값: .env 파일의 ENVIRONMENT 값)"
    echo ""
    echo "예시:"
    echo "  ./deploy.sh dev     # 개발 환경에 배포"
    echo "  ./deploy.sh prod    # 프로덕션 환경에 배포"
    echo ""
    echo "필수 요구사항:"
    echo "  - AWS CLI 설치 및 설정"
    echo "  - SAM CLI 설치"
    echo "  - jq 설치 (JSON 파싱용)"
    echo "  - .env 파일 설정 (.env.example 참조)"
    echo ""
    echo "환경 변수 파일:"
    echo "  .env 파일을 생성하고 필요한 값들을 설정하세요."
    echo "  cp .env.example .env"
}

# 스크립트 인수 처리
case "${1}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    dev|prod)
        ENVIRONMENT=$1
        main
        ;;
    *)
        log_error "잘못된 환경: ${1}"
        log_info "사용 가능한 환경: dev, prod"
        show_help
        exit 1
        ;;
esac
