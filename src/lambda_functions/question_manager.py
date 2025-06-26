"""
AWS Problem Solver Game - Question Manager Lambda Function
문제 조회, 선택, 관리를 담당하는 Lambda 함수
"""

import json
import boto3
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key, Attr

# 프로젝트 경로 추가
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로컬 모듈 import
try:
    from utils.question_engine import question_engine
    from utils.difficulty_adapter import difficulty_adapter
except ImportError:
    # Lambda 환경에서 import 실패 시 기본 구현 사용
    question_engine = None
    difficulty_adapter = None

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
        
        # OPTIONS 요청 처리 (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # HTTP 메서드와 경로 확인
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        print(f"Processing {http_method} request to {path}")
        
        if http_method == 'GET':
            if '/question/random' in path:
                return get_random_question(event, cors_headers)
            elif '/question/adaptive' in path:
                return get_adaptive_question(event, cors_headers)
            elif '/question/' in path:
                return get_question_by_id(event, cors_headers)
            elif '/questions/category' in path:
                return get_questions_by_category(event, cors_headers)
            elif '/questions/npc' in path:
                return get_questions_by_npc(event, cors_headers)
            elif '/questions/scenario' in path:
                return get_questions_by_scenario(event, cors_headers)
        
        elif http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'validate_answer':
                return validate_answer(body, cors_headers)
            elif action == 'get_question_stats':
                return get_question_statistics(body, cors_headers)
        
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
        print(f"Error in question_manager: {str(e)}")
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

def get_adaptive_question(event, cors_headers) -> Dict:
    """
    적응형 문제 조회 (사용자 실력 기반)
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('userId')
        npc_id = query_params.get('npcId')
        scenario_id = query_params.get('scenarioId')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'userId 파라미터가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # 세션 컨텍스트 구성
        session_context = {}
        if npc_id:
            session_context['npc_id'] = npc_id
        if scenario_id:
            session_context['scenario_id'] = scenario_id
        
        # 적응형 문제 선택
        if question_engine:
            question = question_engine.get_adaptive_question(user_id, session_context)
        else:
            # Fallback: 기본 랜덤 선택
            question = get_fallback_random_question(query_params)
        
        if not question:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '조건에 맞는 문제를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'question': question,
                'adaptive_info': {
                    'user_id': user_id,
                    'selection_method': 'adaptive',
                    'context': session_context
                }
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_adaptive_question: {str(e)}")
        raise

def get_questions_by_npc(event, cors_headers) -> Dict:
    """
    NPC별 맞춤 문제 조회
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        npc_id = query_params.get('npcId')
        count = int(query_params.get('count', 5))
        user_level = int(query_params.get('userLevel', 1))
        
        if not npc_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'npcId 파라미터가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # NPC별 문제 선택
        if question_engine:
            questions = question_engine.get_questions_by_npc(npc_id, count, user_level)
        else:
            # Fallback: NPC 기반 필터링
            questions = get_fallback_npc_questions(npc_id, count)
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'questions': questions,
                'npc_id': npc_id,
                'count': len(questions),
                'user_level': user_level
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_questions_by_npc: {str(e)}")
        raise

def get_questions_by_scenario(event, cors_headers) -> Dict:
    """
    시나리오별 문제 조회
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        scenario_id = query_params.get('scenarioId')
        phase = int(query_params.get('phase', 1))
        
        if not scenario_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'scenarioId 파라미터가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # 시나리오별 문제 선택
        if question_engine:
            questions = question_engine.get_questions_by_scenario(scenario_id, phase)
        else:
            # Fallback: 기본 문제 반환
            questions = []
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'questions': questions,
                'scenario_id': scenario_id,
                'phase': phase,
                'count': len(questions)
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_questions_by_scenario: {str(e)}")
        raise

def validate_answer(data: Dict, cors_headers) -> Dict:
    """
    답안 검증 및 결과 반환
    """
    try:
        question_id = data.get('questionId')
        selected_answer = data.get('selectedAnswer')
        user_id = data.get('userId')
        time_spent = data.get('timeSpent', 0)
        hints_used = data.get('hintsUsed', 0)
        
        if not all([question_id, selected_answer]):
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '필수 파라미터가 누락되었습니다.'
                }, ensure_ascii=False)
            }
        
        # 답안 검증
        if question_engine:
            result = question_engine.validate_answer(
                question_id, selected_answer, user_id, time_spent, hints_used
            )
        else:
            # Fallback: 기본 검증
            result = validate_answer_fallback(question_id, selected_answer, time_spent, hints_used)
        
        if 'error' in result:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps(result, ensure_ascii=False)
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in validate_answer: {str(e)}")
        raise

def get_question_statistics(data: Dict, cors_headers) -> Dict:
    """
    문제 통계 조회
    """
    try:
        question_id = data.get('questionId')
        
        if question_engine:
            stats = question_engine.get_question_statistics(question_id)
        else:
            # Fallback: 기본 통계
            stats = {'message': '통계 기능을 사용할 수 없습니다.'}
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(stats, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_question_statistics: {str(e)}")
        raise

# Fallback 함수들 (question_engine 사용 불가 시)
def get_fallback_random_question(query_params: Dict) -> Optional[Dict]:
    """
    기본 랜덤 문제 선택 (fallback)
    """
    try:
        category = query_params.get('category')
        difficulty = query_params.get('difficulty')
        
        # 필터 조건 구성
        filter_expression = Attr('isActive').eq(True)
        
        if category:
            filter_expression = filter_expression & Attr('category').eq(category)
        if difficulty:
            filter_expression = filter_expression & Attr('difficulty').eq(difficulty)
        
        # DynamoDB 스캔
        response = questions_table.scan(
            FilterExpression=filter_expression,
            Limit=10
        )
        
        questions = response.get('Items', [])
        if not questions:
            return None
        
        # 랜덤 선택
        import random
        selected_question = random.choice(questions)
        return prepare_question_for_client_fallback(selected_question)
        
    except Exception as e:
        print(f"Error in get_fallback_random_question: {str(e)}")
        return None

def get_fallback_npc_questions(npc_id: str, count: int) -> List[Dict]:
    """
    NPC 기반 기본 문제 선택 (fallback)
    """
    try:
        # NPC별 기본 카테고리 매핑
        npc_categories = {
            'alex_ceo': ['EC2', 'S3'],
            'sarah_analyst': ['S3', 'LAMBDA'],
            'mike_security': ['VPC', 'S3'],
            'jenny_developer': ['LAMBDA', 'S3']
        }
        
        categories = npc_categories.get(npc_id, ['EC2'])
        questions = []
        
        for category in categories:
            response = questions_table.scan(
                FilterExpression=Attr('category').eq(category) & Attr('isActive').eq(True),
                Limit=count
            )
            
            for item in response.get('Items', []):
                if len(questions) < count:
                    questions.append(prepare_question_for_client_fallback(item))
        
        return questions
        
    except Exception as e:
        print(f"Error in get_fallback_npc_questions: {str(e)}")
        return []

def validate_answer_fallback(question_id: str, selected_answer: str, time_spent: int, hints_used: int) -> Dict:
    """
    기본 답안 검증 (fallback)
    """
    try:
        # 문제 조회
        response = questions_table.get_item(Key={'questionId': question_id})
        
        if 'Item' not in response:
            return {'error': '문제를 찾을 수 없습니다.'}
        
        question = response['Item']
        
        # 정답 확인
        correct_answer = None
        for option in question.get('options', []):
            if option.get('isCorrect', False):
                correct_answer = option['id']
                break
        
        is_correct = selected_answer == correct_answer
        
        # 기본 점수 계산
        base_points = question.get('points', 100)
        points = base_points if is_correct else 0
        
        return {
            'questionId': question_id,
            'selectedAnswer': selected_answer,
            'correctAnswer': correct_answer,
            'isCorrect': is_correct,
            'explanation': question.get('explanation', ''),
            'score': {
                'points': points,
                'experience': 20 if is_correct else 10,
                'bonus': 0,
                'breakdown': {'base': points, 'difficulty': 0, 'time': 0, 'hint_penalty': 0}
            },
            'timeSpent': time_spent,
            'hintsUsed': hints_used
        }
        
    except Exception as e:
        print(f"Error in validate_answer_fallback: {str(e)}")
        return {'error': '답안 검증 중 오류가 발생했습니다.'}

def prepare_question_for_client_fallback(question: Dict) -> Dict:
    """
    클라이언트용 문제 데이터 준비 (fallback)
    """
    if not question:
        return None
    
    # 선택지에서 정답 정보 제거
    options = []
    for option in question.get('options', []):
        options.append({
            'id': option['id'],
            'text': option['text']
        })
    
    return {
        'questionId': question['questionId'],
        'category': question['category'],
        'difficulty': question['difficulty'],
        'npcCharacter': question['npcCharacter'],
        'scenario': question['scenario'],
        'question': question['question'],
        'options': options,
        'tags': question.get('tags', []),
        'estimatedTime': question.get('estimatedTime', 60),
        'points': question.get('points', 100)
    }
def get_random_question(event, cors_headers) -> Dict:
    """
    랜덤 문제 조회
    쿼리 파라미터: category, difficulty, npc
    """
    try:
        # 쿼리 파라미터 파싱
        query_params = event.get('queryStringParameters') or {}
        
        # question_engine 사용 가능 시
        if question_engine:
            filters = {}
            if query_params.get('category'):
                filters['category'] = query_params['category']
            if query_params.get('difficulty'):
                filters['difficulty'] = query_params['difficulty']
            if query_params.get('npc'):
                filters['npc'] = query_params['npc']
            
            question = question_engine.get_random_question(filters)
        else:
            # Fallback 사용
            question = get_fallback_random_question(query_params)
        
        if not question:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '조건에 맞는 문제를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'question': question,
                'selection_method': 'random',
                'filters_applied': query_params
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_random_question: {str(e)}")
        raise

def get_question_by_id(event) -> Dict:
    """
    특정 ID의 문제 조회
    """
    try:
        # 경로에서 questionId 추출
        path_parts = event['path'].split('/')
        question_id = path_parts[-1]
        
        # DynamoDB에서 문제 조회
        response = questions_table.get_item(
            Key={'questionId': question_id}
        )
        
        if 'Item' not in response:
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
        
        question = response['Item']
        
        # 비활성화된 문제 체크
        if not question.get('isActive', True):
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
        
        # 클라이언트용 데이터 준비
        question_data = prepare_question_for_client(question)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(question_data, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_question_by_id: {str(e)}")
        raise

def get_questions_by_category(event) -> Dict:
    """
    카테고리별 문제 목록 조회
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        category = query_params.get('category')
        difficulty = query_params.get('difficulty')
        limit = int(query_params.get('limit', 10))
        
        if not category:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'category 파라미터가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # GSI를 사용한 쿼리
        if difficulty:
            response = questions_table.query(
                IndexName='category-difficulty-index',
                KeyConditionExpression=Key('category').eq(category) & Key('difficulty').eq(difficulty),
                FilterExpression=Attr('isActive').eq(True),
                Limit=limit
            )
        else:
            response = questions_table.query(
                IndexName='category-difficulty-index',
                KeyConditionExpression=Key('category').eq(category),
                FilterExpression=Attr('isActive').eq(True),
                Limit=limit
            )
        
        questions = response.get('Items', [])
        
        # 클라이언트용 데이터 준비 (목록이므로 간단한 정보만)
        questions_summary = []
        for question in questions:
            questions_summary.append({
                'questionId': question['questionId'],
                'category': question['category'],
                'difficulty': question['difficulty'],
                'npcCharacter': question['npcCharacter'],
                'scenario': {
                    'title': question['scenario']['title']
                },
                'estimatedTime': question.get('estimatedTime', 60),
                'points': question.get('points', 100)
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'questions': questions_summary,
                'count': len(questions_summary),
                'category': category,
                'difficulty': difficulty
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_questions_by_category: {str(e)}")
        raise

def prepare_question_for_client(question: Dict) -> Dict:
    """
    클라이언트에 전송할 문제 데이터 준비 (정답 정보 제외)
    """
    # 선택지에서 정답 정보 제거
    options = []
    for option in question.get('options', []):
        options.append({
            'id': option['id'],
            'text': option['text']
            # isCorrect 필드는 제외
        })
    
    return {
        'questionId': question['questionId'],
        'category': question['category'],
        'difficulty': question['difficulty'],
        'npcCharacter': question['npcCharacter'],
        'scenario': question['scenario'],
        'question': question['question'],
        'options': options,
        'tags': question.get('tags', []),
        'estimatedTime': question.get('estimatedTime', 60),
        'points': question.get('points', 100)
    }

def get_available_categories() -> List[str]:
    """
    사용 가능한 카테고리 목록 반환
    """
    return ['EC2', 'S3', 'RDS', 'VPC', 'Lambda', 'IAM', 'CloudWatch', 'Auto Scaling']

def get_available_difficulties() -> List[str]:
    """
    사용 가능한 난이도 목록 반환
    """
    return ['easy', 'medium', 'hard']

def get_available_npcs() -> List[str]:
    """
    사용 가능한 NPC 캐릭터 목록 반환
    """
    return ['alex_ceo', 'sarah_analyst', 'mike_security', 'jenny_developer']
