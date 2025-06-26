"""
AWS Problem Solver Game - Hint Provider Lambda Function
Amazon Q CLI를 활용한 힌트 제공 시스템
"""

import json
import boto3
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table('aws-game-questions')
users_table = dynamodb.Table('aws-game-users')

"""
AWS Problem Solver Game - Hint Provider Lambda Function
Amazon Q CLI를 활용한 힌트 제공 시스템
"""

import json
import boto3
import subprocess
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 프로젝트 경로 추가
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로컬 모듈 import
try:
    from utils.q_cli_integration import q_cli
    from utils.npc_dialogue_engine import dialogue_engine
except ImportError:
    q_cli = None
    dialogue_engine = None

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table(os.environ.get('QUESTIONS_TABLE', 'aws-game-questions'))
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'aws-game-users'))

def lambda_handler(event, context):
    """
    Lambda 함수 메인 핸들러
    """
    try:
        # CORS 헤더 설정
        cors_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        
        # OPTIONS 요청 처리
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # HTTP 메서드 확인
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        print(f"Processing {http_method} request to {path}")
        
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'get_hint':
                return get_question_hint(body, cors_headers)
            elif action == 'ask_q':
                return ask_amazon_q(body, cors_headers)
            elif action == 'explain_concept':
                return explain_aws_concept(body, cors_headers)
            elif action == 'get_npc_hint':
                return get_npc_hint(body, cors_headers)
            elif action == 'validate_hint_usage':
                return validate_hint_usage(body, cors_headers)
        
        elif http_method == 'GET':
            if '/hint/status' in path:
                return get_hint_system_status(event, cors_headers)
        
        return {
            'statusCode': 404,
            'headers': cors_headers,
            'body': json.dumps({
                'error': '요청한 엔드포인트를 찾을 수 없습니다.',
                'path': path,
                'method': http_method
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in hint_provider: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '서버 내부 오류가 발생했습니다.',
                'details': str(e)
            }, ensure_ascii=False)
        }

def get_npc_hint(data: Dict, cors_headers) -> Dict:
    """
    NPC 캐릭터를 통한 힌트 제공
    """
    try:
        session_id = data.get('sessionId')
        question_data = data.get('questionData', {})
        hint_level = data.get('hintLevel', 1)
        
        if not session_id or not question_data:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '필수 파라미터가 누락되었습니다.'
                }, ensure_ascii=False)
            }
        
        # NPC 대화 엔진을 통한 힌트 제공
        if dialogue_engine:
            npc_hint = dialogue_engine.get_hint_response(session_id, question_data, hint_level)
        else:
            # Fallback: 기본 힌트
            npc_hint = get_basic_hint_fallback(question_data, hint_level)
        
        # 힌트 사용 기록
        record_hint_usage(data.get('userId'), question_data.get('questionId'), hint_level)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(npc_hint, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_npc_hint: {str(e)}")
        raise

def validate_hint_usage(data: Dict, cors_headers) -> Dict:
    """
    힌트 사용 권한 및 제한 검증
    """
    try:
        user_id = data.get('userId')
        question_id = data.get('questionId')
        requested_hint_level = data.get('hintLevel', 1)
        
        if not all([user_id, question_id]):
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '필수 파라미터가 누락되었습니다.'
                }, ensure_ascii=False)
            }
        
        # 사용자 힌트 사용 권한 확인
        user_response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '사용자를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        user = user_response['Item']
        
        # 힌트 사용 설정 확인
        hints_enabled = user.get('preferences', {}).get('hintsEnabled', True)
        if not hints_enabled:
            return {
                'statusCode': 403,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '힌트 사용이 비활성화되어 있습니다.',
                    'can_use_hint': False
                }, ensure_ascii=False)
            }
        
        # 일일 힌트 사용 제한 확인
        daily_hint_limit = user.get('preferences', {}).get('dailyHintLimit', 20)
        daily_hints_used = get_daily_hints_used(user_id)
        
        if daily_hints_used >= daily_hint_limit:
            return {
                'statusCode': 429,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '일일 힌트 사용 한도를 초과했습니다.',
                    'can_use_hint': False,
                    'daily_limit': daily_hint_limit,
                    'used_today': daily_hints_used
                }, ensure_ascii=False)
            }
        
        # 문제별 힌트 제한 확인
        question_hints_used = get_question_hints_used(user_id, question_id)
        max_hints_per_question = 3
        
        if question_hints_used >= max_hints_per_question:
            return {
                'statusCode': 429,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '이 문제에 대한 힌트 사용 한도를 초과했습니다.',
                    'can_use_hint': False,
                    'question_limit': max_hints_per_question,
                    'used_for_question': question_hints_used
                }, ensure_ascii=False)
            }
        
        # 점수 페널티 계산
        penalty = calculate_hint_penalty(question_id, requested_hint_level)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'can_use_hint': True,
                'hint_level': requested_hint_level,
                'points_penalty': penalty,
                'remaining_daily_hints': daily_hint_limit - daily_hints_used,
                'remaining_question_hints': max_hints_per_question - question_hints_used
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in validate_hint_usage: {str(e)}")
        raise

def get_hint_system_status(event, cors_headers) -> Dict:
    """
    힌트 시스템 상태 조회
    """
    try:
        # Amazon Q CLI 사용 가능 여부 확인
        q_cli_available = check_q_cli_availability()
        
        # NPC 대화 엔진 상태 확인
        npc_engine_available = dialogue_engine is not None
        
        # 시스템 통계
        stats = get_hint_system_statistics()
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'system_status': {
                    'q_cli_available': q_cli_available,
                    'npc_engine_available': npc_engine_available,
                    'overall_status': 'healthy' if q_cli_available else 'degraded'
                },
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_hint_system_status: {str(e)}")
        raise

# 헬퍼 함수들
def get_basic_hint_fallback(question_data: Dict, hint_level: int) -> Dict:
    """
    기본 힌트 제공 (fallback)
    """
    hints = question_data.get('hints', [])
    
    if hint_level <= len(hints):
        hint_text = hints[hint_level - 1]
    else:
        hint_text = "추가 힌트를 제공할 수 없습니다. 문제를 다시 한 번 천천히 읽어보세요."
    
    return {
        'session_id': 'fallback',
        'message': hint_text,
        'hint': hint_text,
        'hint_level': hint_level,
        'type': 'basic_hint',
        'source': 'fallback',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def record_hint_usage(user_id: str, question_id: str, hint_level: int):
    """
    힌트 사용 기록
    """
    try:
        if not user_id:
            return
        
        # 사용자 힌트 통계 업데이트
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='ADD stats.hintsUsed :inc',
            ExpressionAttributeValues={':inc': 1}
        )
        
        # 일일 힌트 사용 기록 (별도 테이블이나 캐시 사용 권장)
        # 여기서는 간단히 사용자 속성에 기록
        today = datetime.utcnow().strftime('%Y-%m-%d')
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='ADD dailyHints.#date :inc',
            ExpressionAttributeNames={'#date': today},
            ExpressionAttributeValues={':inc': 1}
        )
        
    except Exception as e:
        print(f"Error recording hint usage: {str(e)}")

def get_daily_hints_used(user_id: str) -> int:
    """
    일일 힌트 사용량 조회
    """
    try:
        response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            return 0
        
        user = response['Item']
        today = datetime.utcnow().strftime('%Y-%m-%d')
        daily_hints = user.get('dailyHints', {})
        
        return daily_hints.get(today, 0)
        
    except Exception as e:
        print(f"Error getting daily hints used: {str(e)}")
        return 0

def get_question_hints_used(user_id: str, question_id: str) -> int:
    """
    특정 문제에 대한 힌트 사용량 조회
    """
    try:
        # 실제 구현에서는 세션 데이터나 별도 테이블에서 조회
        # 여기서는 간단히 0 반환 (구현 필요)
        return 0
        
    except Exception as e:
        print(f"Error getting question hints used: {str(e)}")
        return 0

def calculate_hint_penalty(question_id: str, hint_level: int) -> int:
    """
    힌트 사용에 따른 점수 페널티 계산
    """
    try:
        # 문제 정보 조회
        response = questions_table.get_item(Key={'questionId': question_id})
        if 'Item' not in response:
            return 10  # 기본 페널티
        
        question = response['Item']
        base_points = question.get('points', 100)
        
        # 힌트 레벨에 따른 페널티 (10% * 힌트 레벨)
        penalty_rate = 0.1 * hint_level
        penalty = int(base_points * penalty_rate)
        
        return penalty
        
    except Exception as e:
        print(f"Error calculating hint penalty: {str(e)}")
        return 10

def check_q_cli_availability() -> bool:
    """
    Amazon Q CLI 사용 가능 여부 확인
    """
    try:
        if q_cli:
            return q_cli.cli_available
        else:
            # 직접 확인
            result = subprocess.run(
                ['q', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
    except Exception:
        return False

def get_hint_system_statistics() -> Dict:
    """
    힌트 시스템 통계 조회
    """
    try:
        # 실제 구현에서는 CloudWatch 메트릭스나 별도 통계 테이블에서 조회
        return {
            'total_hints_provided': 0,
            'q_cli_success_rate': 0.95,
            'average_response_time': 1.2,
            'most_requested_categories': ['EC2', 'S3', 'Lambda']
        }
    except Exception as e:
        print(f"Error getting hint system statistics: {str(e)}")
        return {}
    """
    문제별 단계적 힌트 제공
    """
    try:
        user_id = data.get('userId')
        question_id = data.get('questionId')
        hint_level = data.get('hintLevel', 1)  # 1, 2, 3 단계
        
        if not all([user_id, question_id]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '필수 파라미터가 누락되었습니다.'
                }, ensure_ascii=False)
            }
        
        # 문제 정보 조회
        question_response = questions_table.get_item(
            Key={'questionId': question_id}
        )
        
        if 'Item' not in question_response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '문제를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        question = question_response['Item']
        
        # 사용자 힌트 사용 권한 확인
        user_response = users_table.get_item(Key={'userId': user_id})
        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '사용자를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        user = user_response['Item']
        if not user.get('preferences', {}).get('hintsEnabled', True):
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '힌트 사용이 비활성화되어 있습니다.'
                }, ensure_ascii=False)
            }
        
        # 단계별 힌트 제공
        hints = question.get('hints', [])
        
        if hint_level > len(hints):
            # Amazon Q CLI를 통한 동적 힌트 생성
            dynamic_hint = generate_dynamic_hint(question, hint_level)
            hint_text = dynamic_hint
        else:
            hint_text = hints[hint_level - 1]
        
        # 힌트 사용 기록 업데이트
        update_hint_usage(user_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'hint': hint_text,
                'hintLevel': hint_level,
                'maxHints': len(hints) + 2,  # 기본 힌트 + 동적 힌트 2개
                'pointsPenalty': calculate_hint_penalty(question, hint_level)
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_question_hint: {str(e)}")
        raise

def ask_amazon_q(data: Dict) -> Dict:
    """
    Amazon Q CLI를 통한 자유 질문
    """
    try:
        user_id = data.get('userId')
        question_text = data.get('question')
        context = data.get('context', '')  # 현재 문제 컨텍스트
        
        if not all([user_id, question_text]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '필수 파라미터가 누락되었습니다.'
                }, ensure_ascii=False)
            }
        
        # Amazon Q CLI 호출
        q_response = call_amazon_q_cli(question_text, context)
        
        if not q_response:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Amazon Q 서비스에 연결할 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'answer': q_response,
                'source': 'Amazon Q CLI',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in ask_amazon_q: {str(e)}")
        raise

def explain_aws_concept(data: Dict) -> Dict:
    """
    AWS 개념 설명 요청
    """
    try:
        concept = data.get('concept')
        detail_level = data.get('detailLevel', 'basic')  # basic, intermediate, advanced
        
        if not concept:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'concept 파라미터가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # 개념별 맞춤형 질문 생성
        prompt = generate_concept_prompt(concept, detail_level)
        
        # Amazon Q CLI 호출
        explanation = call_amazon_q_cli(prompt)
        
        if not explanation:
            # 기본 설명 제공
            explanation = get_basic_concept_explanation(concept)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'concept': concept,
                'explanation': explanation,
                'detailLevel': detail_level,
                'relatedServices': get_related_services(concept)
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in explain_aws_concept: {str(e)}")
        raise

def call_amazon_q_cli(question: str, context: str = '') -> Optional[str]:
    """
    Amazon Q CLI 호출
    """
    try:
        # 컨텍스트가 있으면 질문에 포함
        if context:
            full_question = f"컨텍스트: {context}\n\n질문: {question}"
        else:
            full_question = question
        
        # Amazon Q CLI 명령어 실행
        # 실제 환경에서는 q chat 명령어를 사용
        cmd = ['q', 'chat', '--message', full_question]
        
        # Lambda 환경에서는 subprocess 사용에 제한이 있을 수 있음
        # 실제 구현에서는 AWS SDK나 API를 사용해야 할 수 있음
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=dict(os.environ)
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Q CLI error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Q CLI timeout")
            return None
        except FileNotFoundError:
            print("Q CLI not found")
            return None
            
    except Exception as e:
        print(f"Error calling Amazon Q CLI: {str(e)}")
        return None

def generate_dynamic_hint(question: Dict, hint_level: int) -> str:
    """
    Amazon Q CLI를 활용한 동적 힌트 생성
    """
    try:
        category = question.get('category', '')
        difficulty = question.get('difficulty', '')
        scenario = question.get('scenario', {})
        
        # 힌트 레벨에 따른 프롬프트 생성
        if hint_level == 4:  # 첫 번째 동적 힌트
            prompt = f"""
            AWS {category} 서비스와 관련된 다음 시나리오에 대해 해결 방향을 제시해주세요:
            
            시나리오: {scenario.get('description', '')}
            
            힌트는 직접적인 답을 주지 말고, 고려해야 할 AWS 서비스나 개념을 제안하는 형태로 작성해주세요.
            """
        else:  # 두 번째 동적 힌트
            prompt = f"""
            AWS {category} 관련 문제에서 {difficulty} 난이도 수준의 모범 사례를 간단히 설명해주세요.
            
            컨텍스트: {scenario.get('context', '')}
            
            구체적인 서비스 이름보다는 아키텍처 패턴이나 설계 원칙에 대해 설명해주세요.
            """
        
        # Amazon Q CLI 호출
        dynamic_hint = call_amazon_q_cli(prompt)
        
        if dynamic_hint:
            return dynamic_hint
        else:
            # 기본 힌트 반환
            return get_fallback_hint(category, difficulty)
            
    except Exception as e:
        print(f"Error generating dynamic hint: {str(e)}")
        return get_fallback_hint(question.get('category', ''), question.get('difficulty', ''))

def generate_concept_prompt(concept: str, detail_level: str) -> str:
    """
    개념 설명을 위한 프롬프트 생성
    """
    level_descriptions = {
        'basic': '초보자도 이해할 수 있도록 간단하게',
        'intermediate': '실무에서 활용할 수 있는 수준으로',
        'advanced': '깊이 있는 기술적 세부사항을 포함하여'
    }
    
    return f"""
    AWS {concept}에 대해 {level_descriptions.get(detail_level, '간단하게')} 설명해주세요.
    
    다음 내용을 포함해주세요:
    1. 기본 개념과 목적
    2. 주요 기능과 특징
    3. 사용 사례
    4. 관련 서비스와의 연관성
    
    설명은 한국어로 작성하고, 실무 예시를 포함해주세요.
    """

def get_basic_concept_explanation(concept: str) -> str:
    """
    기본 개념 설명 (Amazon Q CLI 실패 시 대체)
    """
    basic_explanations = {
        'EC2': 'Amazon EC2는 클라우드에서 가상 서버를 제공하는 서비스입니다. 필요에 따라 컴퓨팅 용량을 조절할 수 있어 비용 효율적입니다.',
        'S3': 'Amazon S3는 객체 스토리지 서비스로, 웹사이트, 모바일 앱, 백업 등 다양한 용도로 데이터를 저장할 수 있습니다.',
        'RDS': 'Amazon RDS는 관리형 관계형 데이터베이스 서비스로, MySQL, PostgreSQL 등 다양한 데이터베이스 엔진을 지원합니다.',
        'Lambda': 'AWS Lambda는 서버리스 컴퓨팅 서비스로, 서버 관리 없이 코드를 실행할 수 있습니다.',
        'VPC': 'Amazon VPC는 가상 프라이빗 클라우드로, AWS 클라우드 내에서 논리적으로 격리된 네트워크를 구성할 수 있습니다.'
    }
    
    return basic_explanations.get(concept, f'{concept}에 대한 기본 설명을 준비 중입니다.')

def get_related_services(concept: str) -> List[str]:
    """
    관련 서비스 목록 반환
    """
    related_services = {
        'EC2': ['Auto Scaling', 'Elastic Load Balancing', 'CloudWatch', 'VPC'],
        'S3': ['CloudFront', 'Lambda', 'Athena', 'Glacier'],
        'RDS': ['ElastiCache', 'DynamoDB', 'Aurora', 'Database Migration Service'],
        'Lambda': ['API Gateway', 'S3', 'DynamoDB', 'CloudWatch'],
        'VPC': ['EC2', 'NAT Gateway', 'Internet Gateway', 'Route 53']
    }
    
    return related_services.get(concept, [])

def get_fallback_hint(category: str, difficulty: str) -> str:
    """
    기본 힌트 (Amazon Q CLI 실패 시 대체)
    """
    fallback_hints = {
        'EC2': {
            'easy': 'EC2 인스턴스의 크기나 개수를 조절하는 방법을 생각해보세요.',
            'medium': '트래픽 분산과 자동 확장을 위한 AWS 서비스들을 고려해보세요.',
            'hard': '고가용성과 내결함성을 위한 멀티 AZ 구성을 생각해보세요.'
        },
        'S3': {
            'easy': 'S3의 스토리지 클래스별 특징을 생각해보세요.',
            'medium': 'S3의 보안 기능과 액세스 제어 방법을 고려해보세요.',
            'hard': 'S3의 성능 최적화와 비용 효율성을 함께 고려해보세요.'
        }
    }
    
    return fallback_hints.get(category, {}).get(difficulty, '문제를 다시 한 번 천천히 읽어보세요.')

def calculate_hint_penalty(question: Dict, hint_level: int) -> int:
    """
    힌트 사용에 따른 점수 페널티 계산
    """
    base_points = question.get('points', 100)
    penalty_rate = 0.1  # 힌트당 10% 페널티
    
    return int(base_points * penalty_rate * hint_level)

def update_hint_usage(user_id: str):
    """
    사용자 힌트 사용 통계 업데이트
    """
    try:
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='ADD stats.hintsUsed :inc',
            ExpressionAttributeValues={':inc': 1}
        )
    except Exception as e:
        print(f"Error updating hint usage: {str(e)}")
