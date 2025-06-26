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

def lambda_handler(event, context):
    """
    Lambda 함수 메인 핸들러
    """
    try:
        # HTTP 메서드 확인
        http_method = event.get('httpMethod', '')
        
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'get_hint':
                return get_question_hint(body)
            elif action == 'ask_q':
                return ask_amazon_q(body)
            elif action == 'explain_concept':
                return explain_aws_concept(body)
        
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '요청한 엔드포인트를 찾을 수 없습니다.'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in hint_provider: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '서버 내부 오류가 발생했습니다.'
            }, ensure_ascii=False)
        }

def get_question_hint(data: Dict) -> Dict:
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
