"""
AWS Problem Solver Game - Leaderboard Lambda Function
리더보드 관리 및 순위 시스템을 담당하는 Lambda 함수
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
leaderboard_table = dynamodb.Table('aws-game-leaderboard')
users_table = dynamodb.Table('aws-game-users')

def lambda_handler(event, context):
    """
    Lambda 함수 메인 핸들러
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'GET':
            if '/leaderboard' in path:
                return get_leaderboard(event)
            elif '/user-rank' in path:
                return get_user_rank(event)
        
        elif http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'update_leaderboard':
                return update_leaderboard(body)
        
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
        print(f"Error in leaderboard: {str(e)}")
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

def get_leaderboard(event) -> Dict:
    """
    리더보드 조회
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        leaderboard_type = query_params.get('type', 'alltime')
        limit = int(query_params.get('limit', 10))
        
        # 리더보드 조회 (점수 내림차순)
        response = leaderboard_table.query(
            KeyConditionExpression=Key('leaderboardType').eq(leaderboard_type),
            ScanIndexForward=False,  # 내림차순
            Limit=limit
        )
        
        rankings = response.get('Items', [])
        
        # 순위 번호 추가
        for i, ranking in enumerate(rankings, 1):
            ranking['position'] = i
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'leaderboard': rankings,
                'type': leaderboard_type,
                'count': len(rankings),
                'lastUpdated': datetime.utcnow().isoformat() + 'Z'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_leaderboard: {str(e)}")
        raise

def update_leaderboard(data: Dict) -> Dict:
    """
    리더보드 업데이트
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
        
        # 모든 리더보드 타입 업데이트
        leaderboard_types = ['daily', 'weekly', 'monthly', 'alltime']
        
        for lb_type in leaderboard_types:
            update_user_ranking(user, lb_type)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': '리더보드가 성공적으로 업데이트되었습니다.',
                'userId': user_id
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in update_leaderboard: {str(e)}")
        raise

def update_user_ranking(user: Dict, leaderboard_type: str):
    """
    특정 리더보드 타입에 사용자 순위 업데이트
    """
    try:
        user_id = user['userId']
        score = user.get('totalScore', 0)
        
        # 기존 항목 삭제 (점수가 변경되었을 수 있으므로)
        try:
            existing_response = leaderboard_table.query(
                IndexName='userId-index',
                KeyConditionExpression=Key('userId').eq(user_id),
                FilterExpression=Attr('leaderboardType').eq(leaderboard_type)
            )
            
            for item in existing_response.get('Items', []):
                leaderboard_table.delete_item(
                    Key={
                        'leaderboardType': leaderboard_type,
                        'score': item['score']
                    }
                )
        except Exception as e:
            print(f"Error deleting existing ranking: {str(e)}")
        
        # 새 항목 추가
        leaderboard_table.put_item(
            Item={
                'leaderboardType': leaderboard_type,
                'score': score,
                'userId': user_id,
                'username': user.get('username', f'Player_{user_id[-6:]}'),
                'level': user.get('level', 1),
                'rank': user.get('rank', 'Junior Solutions Architect'),
                'accuracy': user.get('stats', {}).get('accuracy', 0.0),
                'totalQuestions': user.get('stats', {}).get('totalQuestions', 0),
                'achievements': user.get('achievements', []),
                'updatedAt': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
    except Exception as e:
        print(f"Error updating user ranking: {str(e)}")
        raise
