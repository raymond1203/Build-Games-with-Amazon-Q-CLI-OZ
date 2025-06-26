"""
AWS Problem Solver Game - AI Hint Provider
Amazon Q CLI를 활용한 지능형 힌트 시스템
"""

import json
import boto3
import subprocess
import os
from typing import Dict, List, Any, Optional
import logging

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AmazonQHintProvider:
    """Amazon Q CLI를 활용한 힌트 제공 시스템"""
    
    def __init__(self):
        self.q_cli_available = self._check_q_cli_availability()
        
        # NPC별 힌트 스타일 정의
        self.npc_hint_styles = {
            'alex_ceo': {
                'personality': 'energetic_business',
                'style_prompts': [
                    "비즈니스 관점에서 빠르고 효율적인 솔루션을 제안해주세요.",
                    "스타트업 CEO의 입장에서 비용 효율적이면서도 확장 가능한 방법을 알려주세요.",
                    "투자자에게 설명하기 쉬운 명확한 AWS 솔루션을 제시해주세요."
                ]
            },
            'sarah_analyst': {
                'personality': 'analytical_data',
                'style_prompts': [
                    "데이터 분석가 관점에서 체계적이고 정확한 접근법을 설명해주세요.",
                    "데이터 처리와 분석에 최적화된 AWS 서비스 조합을 제안해주세요.",
                    "성능 지표와 모니터링을 고려한 솔루션을 알려주세요."
                ]
            },
            'mike_security': {
                'personality': 'security_focused',
                'style_prompts': [
                    "보안 담당자 관점에서 안전하고 규제 준수가 가능한 방법을 제시해주세요.",
                    "보안 모범 사례를 적용한 AWS 아키텍처를 설명해주세요.",
                    "제로 트러스트 보안 모델을 고려한 솔루션을 알려주세요."
                ]
            },
            'jenny_developer': {
                'personality': 'developer_friendly',
                'style_prompts': [
                    "개발자 친화적이고 자동화된 솔루션을 제안해주세요.",
                    "서버리스와 최신 기술을 활용한 혁신적인 접근법을 알려주세요.",
                    "개발 생산성을 높일 수 있는 AWS 서비스 조합을 설명해주세요."
                ]
            }
        }
        
        # 힌트 레벨별 상세도
        self.hint_levels = {
            1: "간단한 방향성 제시",
            2: "구체적인 서비스 제안",
            3: "상세한 구현 방법"
        }
    
    def _check_q_cli_availability(self) -> bool:
        """Amazon Q CLI 사용 가능 여부 확인"""
        try:
            result = subprocess.run(['q', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Amazon Q CLI not available, using fallback system")
            return False
    
    def generate_hint(self, question_data: Dict[str, Any], 
                     npc_id: str, hint_level: int) -> Dict[str, Any]:
        """
        문제와 NPC에 맞는 힌트 생성
        
        Args:
            question_data: 문제 정보
            npc_id: NPC 식별자
            hint_level: 힌트 레벨 (1-3)
        
        Returns:
            힌트 데이터
        """
        try:
            if self.q_cli_available:
                return self._generate_q_cli_hint(question_data, npc_id, hint_level)
            else:
                return self._generate_fallback_hint(question_data, npc_id, hint_level)
        except Exception as e:
            logger.error(f"Error generating hint: {str(e)}")
            return self._generate_fallback_hint(question_data, npc_id, hint_level)
    
    def _generate_q_cli_hint(self, question_data: Dict[str, Any], 
                           npc_id: str, hint_level: int) -> Dict[str, Any]:
        """Amazon Q CLI를 사용한 힌트 생성"""
        
        # NPC 스타일 가져오기
        npc_style = self.npc_hint_styles.get(npc_id, self.npc_hint_styles['alex_ceo'])
        style_prompt = npc_style['style_prompts'][min(hint_level - 1, len(npc_style['style_prompts']) - 1)]
        
        # 문제 컨텍스트 구성
        context = self._build_question_context(question_data)
        
        # Amazon Q CLI 프롬프트 구성
        q_prompt = f"""
AWS 문제 해결 힌트 요청:

문제 상황: {context['scenario']}
문제: {context['question']}
카테고리: {context['category']}
난이도: {context['difficulty']}

힌트 레벨: {hint_level} ({self.hint_levels[hint_level]})
요청 스타일: {style_prompt}

다음 조건으로 힌트를 제공해주세요:
1. 한국어로 응답
2. 직접적인 정답은 제시하지 말고 방향성만 제시
3. AWS 서비스명과 핵심 개념 포함
4. {npc_style['personality']} 성격 반영
5. 150자 이내로 간결하게

힌트:
"""
        
        try:
            # Amazon Q CLI 실행
            result = subprocess.run([
                'q', 'chat', 
                '--message', q_prompt.strip(),
                '--format', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                hint_text = response_data.get('response', '').strip()
                
                return {
                    'hint': hint_text,
                    'source': 'amazon_q',
                    'npc_id': npc_id,
                    'hint_level': hint_level,
                    'context': context,
                    'success': True
                }
            else:
                logger.error(f"Q CLI error: {result.stderr}")
                return self._generate_fallback_hint(question_data, npc_id, hint_level)
                
        except subprocess.TimeoutExpired:
            logger.error("Q CLI timeout")
            return self._generate_fallback_hint(question_data, npc_id, hint_level)
        except json.JSONDecodeError:
            logger.error("Failed to parse Q CLI response")
            return self._generate_fallback_hint(question_data, npc_id, hint_level)
    
    def _generate_fallback_hint(self, question_data: Dict[str, Any], 
                              npc_id: str, hint_level: int) -> Dict[str, Any]:
        """Amazon Q CLI 사용 불가 시 대체 힌트 생성"""
        
        context = self._build_question_context(question_data)
        category = context['category'].upper()
        
        # 카테고리별 힌트 템플릿
        hint_templates = {
            'EC2': {
                1: "인스턴스 확장성과 로드 밸런싱을 고려해보세요.",
                2: "Auto Scaling Group과 Application Load Balancer 조합을 생각해보세요.",
                3: "다중 AZ 배포와 CloudWatch 모니터링을 포함한 완전한 아키텍처를 설계해보세요."
            },
            'S3': {
                1: "스토리지 클래스와 액세스 패턴을 고려해보세요.",
                2: "Standard-IA, Glacier 등 적절한 스토리지 클래스를 선택해보세요.",
                3: "라이프사이클 정책과 버전 관리를 포함한 완전한 스토리지 전략을 수립해보세요."
            },
            'LAMBDA': {
                1: "서버리스 아키텍처와 이벤트 기반 처리를 고려해보세요.",
                2: "Lambda와 API Gateway, DynamoDB 조합을 생각해보세요.",
                3: "Step Functions를 활용한 워크플로우 오케스트레이션을 포함해보세요."
            },
            'RDS': {
                1: "데이터베이스 가용성과 백업 전략을 고려해보세요.",
                2: "Multi-AZ 배포와 Read Replica를 생각해보세요.",
                3: "자동 백업, 모니터링, 성능 최적화를 포함한 완전한 DB 솔루션을 설계해보세요."
            },
            'VPC': {
                1: "네트워크 보안과 서브넷 구성을 고려해보세요.",
                2: "퍼블릭/프라이빗 서브넷과 NAT Gateway를 생각해보세요.",
                3: "보안 그룹, NACL, VPC 엔드포인트를 포함한 완전한 네트워크 아키텍처를 설계해보세요."
            }
        }
        
        # 기본 힌트
        default_hints = {
            1: "AWS의 관리형 서비스를 활용해보세요.",
            2: "고가용성과 비용 효율성을 동시에 고려해보세요.",
            3: "모니터링과 자동화를 포함한 완전한 솔루션을 설계해보세요."
        }
        
        # 힌트 선택
        base_hint = hint_templates.get(category, default_hints).get(hint_level, default_hints[hint_level])
        
        # NPC 스타일 적용
        npc_style = self.npc_hint_styles.get(npc_id, self.npc_hint_styles['alex_ceo'])
        styled_hint = self._apply_npc_style(base_hint, npc_id, npc_style)
        
        return {
            'hint': styled_hint,
            'source': 'fallback',
            'npc_id': npc_id,
            'hint_level': hint_level,
            'context': context,
            'success': True
        }
    
    def _apply_npc_style(self, base_hint: str, npc_id: str, npc_style: Dict) -> str:
        """NPC 성격에 맞게 힌트 스타일 적용"""
        
        style_modifiers = {
            'alex_ceo': {
                'prefix': ["빠르게 해결해야 해요! ", "비즈니스 관점에서 ", "투자자들이 좋아할 만한 "],
                'suffix': [" 시간이 중요해요!", " 이게 가장 효율적일 거예요!", " 바로 적용해봅시다!"]
            },
            'sarah_analyst': {
                'prefix': ["데이터를 분석해보니 ", "체계적으로 접근하면 ", "정확한 방법은 "],
                'suffix': [" 이 방법이 가장 안정적입니다.", " 성능 지표도 좋을 거예요.", " 모니터링도 잊지 마세요."]
            },
            'mike_security': {
                'prefix': ["보안을 위해서는 ", "안전한 방법으로 ", "규제 준수를 위해 "],
                'suffix': [" 보안이 최우선이에요.", " 이 방법이 가장 안전합니다.", " 감사 요구사항도 만족해요."]
            },
            'jenny_developer': {
                'prefix': ["개발자 친화적으로 ", "자동화를 활용해서 ", "최신 기술로 "],
                'suffix': [" 개발이 훨씬 쉬워질 거예요!", " 정말 혁신적인 방법이에요!", " 코드 관리도 편해집니다!"]
            }
        }
        
        modifiers = style_modifiers.get(npc_id, style_modifiers['alex_ceo'])
        
        import random
        prefix = random.choice(modifiers['prefix'])
        suffix = random.choice(modifiers['suffix'])
        
        return f"{prefix}{base_hint}{suffix}"
    
    def _build_question_context(self, question_data: Dict[str, Any]) -> Dict[str, str]:
        """문제 데이터에서 컨텍스트 추출"""
        return {
            'category': question_data.get('category', 'General'),
            'difficulty': question_data.get('difficulty', 'medium'),
            'scenario': question_data.get('scenario', {}).get('description', ''),
            'question': question_data.get('question', ''),
            'context': question_data.get('scenario', {}).get('context', '')
        }
    
    def get_aws_explanation(self, service_name: str, context: str = "") -> Dict[str, Any]:
        """AWS 서비스에 대한 상세 설명 제공"""
        
        if self.q_cli_available:
            return self._get_q_cli_explanation(service_name, context)
        else:
            return self._get_fallback_explanation(service_name, context)
    
    def _get_q_cli_explanation(self, service_name: str, context: str) -> Dict[str, Any]:
        """Amazon Q CLI를 사용한 AWS 서비스 설명"""
        
        prompt = f"""
AWS 서비스 설명 요청:

서비스: {service_name}
컨텍스트: {context}

다음 형식으로 한국어로 설명해주세요:
1. 서비스 개요 (2-3문장)
2. 주요 기능 (3-4개 항목)
3. 사용 사례 (2-3개)
4. 관련 서비스 (2-3개)
5. 모범 사례 (2-3개 팁)

간결하고 실용적으로 설명해주세요.
"""
        
        try:
            result = subprocess.run([
                'q', 'chat',
                '--message', prompt.strip(),
                '--format', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                explanation = response_data.get('response', '').strip()
                
                return {
                    'explanation': explanation,
                    'service': service_name,
                    'source': 'amazon_q',
                    'success': True
                }
            else:
                return self._get_fallback_explanation(service_name, context)
                
        except Exception as e:
            logger.error(f"Error getting Q CLI explanation: {str(e)}")
            return self._get_fallback_explanation(service_name, context)
    
    def _get_fallback_explanation(self, service_name: str, context: str) -> Dict[str, Any]:
        """대체 AWS 서비스 설명"""
        
        explanations = {
            'EC2': {
                'overview': 'Amazon EC2는 클라우드에서 확장 가능한 컴퓨팅 용량을 제공하는 웹 서비스입니다.',
                'features': ['다양한 인스턴스 타입', 'Auto Scaling', 'Elastic Load Balancing', 'EBS 스토리지'],
                'use_cases': ['웹 애플리케이션 호스팅', '데이터 처리', '개발/테스트 환경'],
                'related': ['ELB', 'Auto Scaling', 'CloudWatch'],
                'best_practices': ['적절한 인스턴스 타입 선택', '보안 그룹 설정', '정기적인 백업']
            },
            'S3': {
                'overview': 'Amazon S3는 업계 최고의 확장성, 데이터 가용성, 보안 및 성능을 제공하는 객체 스토리지 서비스입니다.',
                'features': ['무제한 스토리지', '다양한 스토리지 클래스', '버전 관리', '라이프사이클 정책'],
                'use_cases': ['정적 웹사이트 호스팅', '데이터 백업', 'CDN 원본 스토리지'],
                'related': ['CloudFront', 'Lambda', 'Glacier'],
                'best_practices': ['적절한 스토리지 클래스 선택', '버킷 정책 설정', '암호화 활성화']
            },
            'Lambda': {
                'overview': 'AWS Lambda는 서버를 프로비저닝하거나 관리하지 않고도 코드를 실행할 수 있는 서버리스 컴퓨팅 서비스입니다.',
                'features': ['자동 스케일링', '이벤트 기반 실행', '다양한 런타임 지원', '내장 모니터링'],
                'use_cases': ['API 백엔드', '데이터 처리', '실시간 파일 처리'],
                'related': ['API Gateway', 'DynamoDB', 'S3'],
                'best_practices': ['함수 크기 최적화', '환경 변수 활용', '적절한 메모리 설정']
            }
        }
        
        service_info = explanations.get(service_name.upper(), explanations['EC2'])
        
        formatted_explanation = f"""
**{service_name} 개요**
{service_info['overview']}

**주요 기능**
{' • '.join(service_info['features'])}

**사용 사례**
{' • '.join(service_info['use_cases'])}

**관련 서비스**
{' • '.join(service_info['related'])}

**모범 사례**
{' • '.join(service_info['best_practices'])}
"""
        
        return {
            'explanation': formatted_explanation.strip(),
            'service': service_name,
            'source': 'fallback',
            'success': True
        }


def lambda_handler(event, context):
    """Lambda 함수 핸들러"""
    
    try:
        # CORS 헤더
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        # OPTIONS 요청 처리 (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # 요청 데이터 파싱
        if event.get('body'):
            request_data = json.loads(event['body'])
        else:
            request_data = event
        
        action = request_data.get('action')
        hint_provider = AmazonQHintProvider()
        
        if action == 'get_hint':
            # 힌트 요청 처리
            question_data = request_data.get('questionData', {})
            npc_id = request_data.get('npcId', 'alex_ceo')
            hint_level = request_data.get('hintLevel', 1)
            
            result = hint_provider.generate_hint(question_data, npc_id, hint_level)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(result)
            }
        
        elif action == 'get_explanation':
            # AWS 서비스 설명 요청 처리
            service_name = request_data.get('serviceName', '')
            context = request_data.get('context', '')
            
            result = hint_provider.get_aws_explanation(service_name, context)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid action'})
            }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


# 로컬 테스트용
if __name__ == "__main__":
    # 테스트 데이터
    test_event = {
        'action': 'get_hint',
        'questionData': {
            'category': 'EC2',
            'difficulty': 'medium',
            'scenario': {
                'description': '웹 애플리케이션의 트래픽이 급증하고 있습니다.',
                'context': '단일 EC2 인스턴스에서 실행 중이며 CPU 사용률이 90%를 넘고 있습니다.'
            },
            'question': '이 상황에서 가장 적절한 AWS 솔루션은 무엇입니까?'
        },
        'npcId': 'alex_ceo',
        'hintLevel': 1
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
