"""
AWS Problem Solver Game - Score Calculator Lambda Function
점수 계산, 레벨 관리, 성취도 처리를 담당하는 Lambda 함수
"""

import json
import boto3
from datetime import datetime
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('aws-game-users')
sessions_table = dynamodb.Table('aws-game-sessions')
questions_table = dynamodb.Table('aws-game-questions')

def lambda_handler(event, context):
    """
    Lambda 함수 메인 핸들러
    """
    try:
        # HTTP 메서드와 경로 확인
        http_method = event.get('httpMethod', '')
        
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'submit_answer':
                return submit_answer(body)
            elif action == 'complete_session':
                return complete_session(body)
            elif action == 'calculate_level':
                return calculate_user_level(body)
        
        elif http_method == 'GET':
            if '/user/' in event.get('path', ''):
                return get_user_stats(event)
        
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
        print(f"Error in score_calculator: {str(e)}")
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

def submit_answer(data: Dict) -> Dict:
    """
    답안 제출 및 점수 계산
    """
    try:
        user_id = data.get('userId')
        question_id = data.get('questionId')
        selected_answer = data.get('selectedAnswer')
        time_spent = data.get('timeSpent', 0)
        hints_used = data.get('hintsUsed', 0)
        
        if not all([user_id, question_id, selected_answer]):
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
        
        # 정답 확인
        correct_answer = None
        for option in question['options']:
            if option.get('isCorrect', False):
                correct_answer = option['id']
                break
        
        is_correct = selected_answer == correct_answer
        
        # 점수 계산
        score_result = calculate_score(
            question=question,
            is_correct=is_correct,
            time_spent=time_spent,
            hints_used=hints_used
        )
        
        # 사용자 통계 업데이트
        update_user_stats(user_id, score_result, is_correct)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'isCorrect': is_correct,
                'correctAnswer': correct_answer,
                'explanation': question.get('explanation', ''),
                'score': score_result,
                'timeSpent': time_spent,
                'hintsUsed': hints_used
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in submit_answer: {str(e)}")
        raise

def calculate_score(question: Dict, is_correct: bool, time_spent: int, hints_used: int) -> Dict:
    """
    점수 계산 로직
    """
    base_points = question.get('points', 100)
    difficulty_multiplier = {
        'easy': 1.0,
        'medium': 1.5,
        'hard': 2.0
    }
    
    if not is_correct:
        return {
            'points': 0,
            'experience': 10,  # 틀려도 경험치는 조금 획득
            'bonus': 0,
            'breakdown': {
                'base': 0,
                'difficulty': 0,
                'time': 0,
                'hint_penalty': 0
            }
        }
    
    # 기본 점수
    difficulty = question.get('difficulty', 'medium')
    difficulty_points = int(base_points * difficulty_multiplier.get(difficulty, 1.0))
    
    # 시간 보너스 (빠르게 답할수록 보너스)
    estimated_time = question.get('estimatedTime', 60)
    time_bonus = 0
    if time_spent < estimated_time * 0.5:  # 예상 시간의 50% 이내
        time_bonus = int(difficulty_points * 0.3)
    elif time_spent < estimated_time * 0.8:  # 예상 시간의 80% 이내
        time_bonus = int(difficulty_points * 0.1)
    
    # 힌트 사용 페널티
    hint_penalty = hints_used * int(difficulty_points * 0.1)
    
    # 최종 점수 계산
    total_points = max(0, difficulty_points + time_bonus - hint_penalty)
    experience = int(total_points * 0.5) + 20  # 경험치는 점수의 50% + 기본 20
    
    return {
        'points': total_points,
        'experience': experience,
        'bonus': time_bonus,
        'breakdown': {
            'base': base_points,
            'difficulty': difficulty_points - base_points,
            'time': time_bonus,
            'hint_penalty': -hint_penalty
        }
    }

def update_user_stats(user_id: str, score_result: Dict, is_correct: bool):
    """
    사용자 통계 업데이트
    """
    try:
        # 현재 사용자 정보 조회
        user_response = users_table.get_item(
            Key={'userId': user_id}
        )
        
        if 'Item' not in user_response:
            # 새 사용자 생성
            create_new_user(user_id)
            user_response = users_table.get_item(Key={'userId': user_id})
        
        user = user_response['Item']
        
        # 통계 업데이트
        stats = user.get('stats', {})
        stats['totalQuestions'] = stats.get('totalQuestions', 0) + 1
        
        if is_correct:
            stats['correctAnswers'] = stats.get('correctAnswers', 0) + 1
        
        stats['accuracy'] = round((stats['correctAnswers'] / stats['totalQuestions']) * 100, 1)
        
        # 경험치 및 점수 업데이트
        new_experience = user.get('experience', 0) + score_result['experience']
        new_total_score = user.get('totalScore', 0) + score_result['points']
        
        # 레벨 계산
        new_level = calculate_level_from_experience(new_experience)
        new_rank = get_rank_from_level(new_level)
        
        # DynamoDB 업데이트
        users_table.update_item(
            Key={'userId': user_id},
            UpdateExpression="""
                SET experience = :exp,
                    totalScore = :score,
                    #level = :level,
                    #rank = :rank,
                    stats = :stats,
                    lastLoginAt = :now
            """,
            ExpressionAttributeNames={
                '#level': 'level',
                '#rank': 'rank'
            },
            ExpressionAttributeValues={
                ':exp': new_experience,
                ':score': new_total_score,
                ':level': new_level,
                ':rank': new_rank,
                ':stats': stats,
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
    except Exception as e:
        print(f"Error updating user stats: {str(e)}")
        raise

def calculate_level_from_experience(experience: int) -> int:
    """
    경험치로부터 레벨 계산
    """
    # 레벨별 필요 경험치 (누적)
    level_thresholds = [
        0,      # Level 1
        100,    # Level 2
        300,    # Level 3
        600,    # Level 4
        1000,   # Level 5
        1500,   # Level 6
        2100,   # Level 7
        2800,   # Level 8
        3600,   # Level 9
        4500,   # Level 10
        5500,   # Level 11
        6600,   # Level 12
        7800,   # Level 13
        9100,   # Level 14
        10500   # Level 15
    ]
    
    for level, threshold in enumerate(level_thresholds, 1):
        if experience < threshold:
            return level - 1
    
    return len(level_thresholds)  # 최대 레벨

def get_rank_from_level(level: int) -> str:
    """
    레벨로부터 등급 계산
    """
    if level <= 3:
        return "Junior Solutions Architect"
    elif level <= 6:
        return "Solutions Architect"
    elif level <= 9:
        return "Senior Solutions Architect"
    elif level <= 12:
        return "Principal Solutions Architect"
    else:
        return "Distinguished Solutions Architect"

def create_new_user(user_id: str):
    """
    새 사용자 생성
    """
    now = datetime.utcnow().isoformat() + 'Z'
    
    users_table.put_item(
        Item={
            'userId': user_id,
            'username': f'Player_{user_id[-6:]}',
            'level': 1,
            'experience': 0,
            'totalScore': 0,
            'rank': 'Junior Solutions Architect',
            'stats': {
                'totalQuestions': 0,
                'correctAnswers': 0,
                'accuracy': 0.0,
                'averageTime': 0.0,
                'hintsUsed': 0,
                'streakRecord': 0
            },
            'achievements': [],
            'preferences': {
                'difficulty': 'medium',
                'categories': [],
                'hintsEnabled': True
            },
            'createdAt': now,
            'lastLoginAt': now,
            'isActive': True
        }
    )

def get_user_stats(event) -> Dict:
    """
    사용자 통계 조회
    """
    try:
        # 경로에서 userId 추출
        path_parts = event['path'].split('/')
        user_id = path_parts[-1]
        
        # 사용자 정보 조회
        response = users_table.get_item(
            Key={'userId': user_id}
        )
        
        if 'Item' not in response:
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
        
        user = response['Item']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(user, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_user_stats: {str(e)}")
        raise

def complete_session(data: Dict) -> Dict:
    """
    게임 세션 완료 처리
    """
    try:
        session_id = data.get('sessionId')
        user_id = data.get('userId')
        session_summary = data.get('summary', {})
        
        # 세션 정보 업데이트
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression="""
                SET #status = :status,
                    summary = :summary,
                    completedAt = :now
            """,
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'completed',
                ':summary': session_summary,
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': '세션이 성공적으로 완료되었습니다.',
                'sessionId': session_id
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in complete_session: {str(e)}")
        raise

def calculate_user_level(data: Dict) -> Dict:
    """
    사용자 레벨 재계산
    """
    try:
        user_id = data.get('userId')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'userId가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # 사용자 정보 조회
        response = users_table.get_item(
            Key={'userId': user_id}
        )
        
        if 'Item' not in response:
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
        
        user = response['Item']
        experience = user.get('experience', 0)
        
        # 레벨 및 등급 계산
        new_level = calculate_level_from_experience(experience)
        new_rank = get_rank_from_level(new_level)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'userId': user_id,
                'experience': experience,
                'level': new_level,
                'rank': new_rank,
                'nextLevelExp': get_next_level_experience(new_level)
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in calculate_user_level: {str(e)}")
        raise

def get_next_level_experience(current_level: int) -> int:
    """
    다음 레벨까지 필요한 경험치 반환
    """
    level_thresholds = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500, 6600, 7800, 9100, 10500]
    
    if current_level < len(level_thresholds):
        return level_thresholds[current_level]
    else:
        return level_thresholds[-1]  # 최대 레벨
