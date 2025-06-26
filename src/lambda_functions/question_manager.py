"""
AWS Problem Solver Game - Question Manager Lambda Function
문제 조회, 선택, 관리를 담당하는 Lambda 함수
"""

import json
import boto3
import random
from datetime import datetime
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table('aws-game-questions')

def lambda_handler(event, context):
    """
    Lambda 함수 메인 핸들러
    """
    try:
        # HTTP 메서드와 경로 확인
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'GET':
            if '/question/random' in path:
                return get_random_question(event)
            elif '/question/' in path:
                return get_question_by_id(event)
            elif '/questions/category' in path:
                return get_questions_by_category(event)
        
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
        print(f"Error in question_manager: {str(e)}")
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

def get_random_question(event) -> Dict:
    """
    랜덤 문제 조회
    쿼리 파라미터: category, difficulty, npc
    """
    try:
        # 쿼리 파라미터 파싱
        query_params = event.get('queryStringParameters') or {}
        category = query_params.get('category')
        difficulty = query_params.get('difficulty')
        npc_character = query_params.get('npc')
        
        # 필터 조건 구성
        filter_expression = Attr('isActive').eq(True)
        
        if category:
            filter_expression = filter_expression & Attr('category').eq(category)
        if difficulty:
            filter_expression = filter_expression & Attr('difficulty').eq(difficulty)
        if npc_character:
            filter_expression = filter_expression & Attr('npcCharacter').eq(npc_character)
        
        # DynamoDB 스캔 (소규모 데이터셋이므로 스캔 사용)
        response = questions_table.scan(
            FilterExpression=filter_expression
        )
        
        questions = response.get('Items', [])
        
        if not questions:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '조건에 맞는 문제를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        # 랜덤 문제 선택
        selected_question = random.choice(questions)
        
        # 클라이언트에 전송할 데이터 정리 (정답 제외)
        question_data = prepare_question_for_client(selected_question)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(question_data, ensure_ascii=False)
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
