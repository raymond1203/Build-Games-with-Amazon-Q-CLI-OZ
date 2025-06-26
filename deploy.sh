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

# 환경 변수 설정
ENVIRONMENT=${1:-dev}
STACK_NAME="aws-problem-solver-game-${ENVIRONMENT}"
REGION=${AWS_DEFAULT_REGION:-us-east-1}

log_info "AWS Problem Solver Game 배포 시작"
log_info "Environment: ${ENVIRONMENT}"
log_info "Stack Name: ${STACK_NAME}"
log_info "Region: ${REGION}"

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
    else
        log_warning "Amazon Q CLI가 설치되지 않았습니다."
        log_info "대체 힌트 시스템이 사용됩니다."
        log_info "Amazon Q CLI 설치: https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/cli-install.html"
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
    
    if sam deploy \
        --stack-name "${STACK_NAME}" \
        --region "${REGION}" \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides Environment="${ENVIRONMENT}" \
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
    
    log_success "스택 출력 정보:"
    echo "  API Gateway URL: ${API_URL}"
    echo "  S3 Bucket: ${BUCKET_NAME}"
    echo "  CloudFront URL: https://${CDN_URL}"
}

# 프론트엔드 배포
deploy_frontend() {
    log_info "프론트엔드 파일 S3에 업로드 중..."
    
    # API URL을 JavaScript 파일에 업데이트
    if [ -f "src/frontend/game.js" ]; then
        sed -i.bak "s|https://your-api-id.execute-api.region.amazonaws.com/dev|${API_URL}|g" src/frontend/game.js
        log_info "API URL 업데이트 완료"
    fi
    
    # S3에 파일 업로드
    if aws s3 sync src/frontend/ "s3://${BUCKET_NAME}/" \
        --region "${REGION}" \
        --delete \
        --cache-control "max-age=86400"; then
        log_success "프론트엔드 배포 완료"
    else
        log_error "프론트엔드 배포 실패"
        exit 1
    fi
    
    # 백업 파일 정리
    if [ -f "src/frontend/game.js.bak" ]; then
        mv src/frontend/game.js.bak src/frontend/game.js
    fi
}

# CloudFront 캐시 무효화
invalidate_cloudfront() {
    log_info "CloudFront 캐시 무효화 중..."
    
    DISTRIBUTION_ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='AWS Problem Solver Game CDN - ${ENVIRONMENT}'].Id" \
        --output text \
        --region "${REGION}")
    
    if [ -n "${DISTRIBUTION_ID}" ] && [ "${DISTRIBUTION_ID}" != "None" ]; then
        aws cloudfront create-invalidation \
            --distribution-id "${DISTRIBUTION_ID}" \
            --paths "/*" \
            --region "${REGION}" > /dev/null
        log_success "CloudFront 캐시 무효화 완료"
    else
        log_warning "CloudFront 배포를 찾을 수 없습니다."
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
    
    # S3 웹사이트 테스트
    if curl -s -o /dev/null -w "%{http_code}" "https://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com/" | grep -q "200"; then
        log_success "S3 웹사이트 응답 확인"
    else
        log_warning "S3 웹사이트 테스트 실패"
    fi
}

# 배포 정보 출력
print_deployment_info() {
    log_success "배포 완료!"
    echo ""
    echo "=== 배포 정보 ==="
    echo "Environment: ${ENVIRONMENT}"
    echo "Stack Name: ${STACK_NAME}"
    echo "Region: ${REGION}"
    echo ""
    echo "=== 접속 URL ==="
    echo "게임 URL (S3): https://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com/"
    echo "게임 URL (CDN): https://${CDN_URL}"
    echo "API URL: ${API_URL}"
    echo ""
    echo "=== 테스트 파일 ==="
    echo "NPC 시스템 테스트: https://${CDN_URL}/test_npc_system.html"
    echo "문제 시스템 테스트: https://${CDN_URL}/test_question_system.html"
    echo "레벨 시스템 테스트: https://${CDN_URL}/test_level_system.html"
    echo "Amazon Q 통합 테스트: https://${CDN_URL}/test_amazon_q_integration.html"
    echo ""
    echo "=== 다음 단계 ==="
    echo "1. Amazon Q CLI 설치 및 설정 (선택사항)"
    echo "2. 게임 URL에 접속하여 테스트"
    echo "3. 필요시 추가 설정 및 커스터마이징"
}

# 메인 실행 함수
main() {
    check_requirements
    check_amazon_q
    build_sam
    deploy_sam
    get_stack_outputs
    deploy_frontend
    invalidate_cloudfront
    test_deployment
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
    echo "  environment    배포 환경 (dev 또는 prod, 기본값: dev)"
    echo ""
    echo "예시:"
    echo "  ./deploy.sh dev     # 개발 환경에 배포"
    echo "  ./deploy.sh prod    # 프로덕션 환경에 배포"
    echo ""
    echo "필수 요구사항:"
    echo "  - AWS CLI 설치 및 설정"
    echo "  - SAM CLI 설치"
    echo "  - jq 설치 (JSON 파싱용)"
    echo "  - curl 설치 (테스트용)"
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
        main
        ;;
    *)
        log_error "잘못된 환경: ${1}"
        log_info "사용 가능한 환경: dev, prod"
        exit 1
        ;;
esac
