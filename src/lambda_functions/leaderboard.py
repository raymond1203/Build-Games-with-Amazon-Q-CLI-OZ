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

"""
AWS Problem Solver Game - Leaderboard Lambda Function
리더보드 관리 및 순위 시스템을 담당하는 Lambda 함수
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
leaderboard_table = dynamodb.Table(os.environ.get('LEADERBOARD_TABLE', 'aws-game-leaderboard'))
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
        
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        print(f"Processing {http_method} request to {path}")
        
        if http_method == 'GET':
            if '/leaderboard' in path:
                return get_leaderboard(event, cors_headers)
            elif '/user-rank' in path:
                return get_user_rank(event, cors_headers)
            elif '/leaderboard/stats' in path:
                return get_leaderboard_stats(event, cors_headers)
        
        elif http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'update_leaderboard':
                return update_leaderboard(body, cors_headers)
            elif action == 'bulk_update':
                return bulk_update_leaderboard(body, cors_headers)
            elif action == 'reset_leaderboard':
                return reset_leaderboard(body, cors_headers)
        
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
        print(f"Error in leaderboard: {str(e)}")
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

def get_user_rank(event, cors_headers) -> Dict:
    """
    특정 사용자의 순위 조회
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('userId')
        leaderboard_type = query_params.get('type', 'alltime')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'userId 파라미터가 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # 사용자의 리더보드 엔트리 조회
        response = leaderboard_table.query(
            IndexName='userId-index',
            KeyConditionExpression=Key('userId').eq(user_id),
            FilterExpression=Attr('leaderboardType').eq(leaderboard_type)
        )
        
        user_entries = response.get('Items', [])
        if not user_entries:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '사용자의 순위 정보를 찾을 수 없습니다.'
                }, ensure_ascii=False)
            }
        
        user_entry = user_entries[0]
        user_score = user_entry['score']
        
        # 해당 사용자보다 높은 점수를 가진 사용자 수 조회 (순위 계산)
        higher_scores_response = leaderboard_table.query(
            KeyConditionExpression=Key('leaderboardType').eq(leaderboard_type) & Key('score').gt(user_score),
            ScanIndexForward=False
        )
        
        rank = len(higher_scores_response.get('Items', [])) + 1
        
        # 전체 참가자 수 조회
        total_response = leaderboard_table.query(
            KeyConditionExpression=Key('leaderboardType').eq(leaderboard_type)
        )
        total_participants = len(total_response.get('Items', []))
        
        # 상위 퍼센트 계산
        percentile = ((total_participants - rank + 1) / total_participants) * 100 if total_participants > 0 else 0
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'user_id': user_id,
                'leaderboard_type': leaderboard_type,
                'rank': rank,
                'score': user_score,
                'total_participants': total_participants,
                'percentile': round(percentile, 1),
                'user_info': {
                    'username': user_entry.get('username', ''),
                    'level': user_entry.get('level', 1),
                    'accuracy': user_entry.get('accuracy', 0)
                }
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_user_rank: {str(e)}")
        raise

def get_leaderboard_stats(event, cors_headers) -> Dict:
    """
    리더보드 통계 조회
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        leaderboard_type = query_params.get('type', 'alltime')
        
        # 리더보드 데이터 조회
        response = leaderboard_table.query(
            KeyConditionExpression=Key('leaderboardType').eq(leaderboard_type),
            ScanIndexForward=False
        )
        
        entries = response.get('Items', [])
        
        if not entries:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'leaderboard_type': leaderboard_type,
                    'statistics': {
                        'total_participants': 0,
                        'average_score': 0,
                        'highest_score': 0,
                        'lowest_score': 0
                    }
                }, ensure_ascii=False)
            }
        
        # 통계 계산
        scores = [entry['score'] for entry in entries]
        levels = [entry.get('level', 1) for entry in entries]
        accuracies = [entry.get('accuracy', 0) for entry in entries]
        
        statistics = {
            'total_participants': len(entries),
            'average_score': round(sum(scores) / len(scores), 1),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'average_level': round(sum(levels) / len(levels), 1),
            'average_accuracy': round(sum(accuracies) / len(accuracies), 1),
            'score_distribution': calculate_score_distribution(scores),
            'level_distribution': calculate_level_distribution(levels),
            'top_performers': entries[:5]  # 상위 5명
        }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'leaderboard_type': leaderboard_type,
                'statistics': statistics,
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in get_leaderboard_stats: {str(e)}")
        raise

def bulk_update_leaderboard(data: Dict, cors_headers) -> Dict:
    """
    리더보드 대량 업데이트
    """
    try:
        user_updates = data.get('userUpdates', [])
        
        if not user_updates:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'userUpdates 배열이 필요합니다.'
                }, ensure_ascii=False)
            }
        
        updated_count = 0
        failed_updates = []
        
        for update in user_updates:
            try:
                user_id = update.get('userId')
                if not user_id:
                    continue
                
                # 사용자 정보 조회
                user_response = users_table.get_item(Key={'userId': user_id})
                if 'Item' not in user_response:
                    failed_updates.append({'userId': user_id, 'reason': 'User not found'})
                    continue
                
                user = user_response['Item']
                
                # 리더보드 업데이트
                update_user_ranking(user, ['alltime', 'monthly', 'weekly', 'daily'])
                updated_count += 1
                
            except Exception as e:
                failed_updates.append({'userId': update.get('userId'), 'reason': str(e)})
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'message': f'{updated_count}명의 사용자 리더보드가 업데이트되었습니다.',
                'updated_count': updated_count,
                'failed_count': len(failed_updates),
                'failed_updates': failed_updates
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in bulk_update_leaderboard: {str(e)}")
        raise

def reset_leaderboard(data: Dict, cors_headers) -> Dict:
    """
    리더보드 초기화 (관리자 전용)
    """
    try:
        leaderboard_type = data.get('leaderboardType')
        admin_key = data.get('adminKey')
        
        # 관리자 키 검증 (실제 환경에서는 더 강력한 인증 필요)
        if admin_key != os.environ.get('ADMIN_KEY', 'default_admin_key'):
            return {
                'statusCode': 403,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': '관리자 권한이 필요합니다.'
                }, ensure_ascii=False)
            }
        
        if not leaderboard_type:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'leaderboardType이 필요합니다.'
                }, ensure_ascii=False)
            }
        
        # 해당 타입의 모든 리더보드 엔트리 삭제
        response = leaderboard_table.query(
            KeyConditionExpression=Key('leaderboardType').eq(leaderboard_type)
        )
        
        deleted_count = 0
        for item in response.get('Items', []):
            leaderboard_table.delete_item(
                Key={
                    'leaderboardType': leaderboard_type,
                    'score': item['score']
                }
            )
            deleted_count += 1
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'message': f'{leaderboard_type} 리더보드가 초기화되었습니다.',
                'deleted_count': deleted_count,
                'leaderboard_type': leaderboard_type
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error in reset_leaderboard: {str(e)}")
        raise

# 헬퍼 함수들
def calculate_score_distribution(scores: List[int]) -> Dict:
    """
    점수 분포 계산
    """
    if not scores:
        return {}
    
    # 점수 구간별 분포
    ranges = {
        '0-999': 0,
        '1000-2499': 0,
        '2500-4999': 0,
        '5000-9999': 0,
        '10000+': 0
    }
    
    for score in scores:
        if score < 1000:
            ranges['0-999'] += 1
        elif score < 2500:
            ranges['1000-2499'] += 1
        elif score < 5000:
            ranges['2500-4999'] += 1
        elif score < 10000:
            ranges['5000-9999'] += 1
        else:
            ranges['10000+'] += 1
    
    return ranges

def calculate_level_distribution(levels: List[int]) -> Dict:
    """
    레벨 분포 계산
    """
    if not levels:
        return {}
    
    # 레벨 구간별 분포
    ranges = {
        '1-3': 0,
        '4-6': 0,
        '7-9': 0,
        '10-12': 0,
        '13+': 0
    }
    
    for level in levels:
        if level <= 3:
            ranges['1-3'] += 1
        elif level <= 6:
            ranges['4-6'] += 1
        elif level <= 9:
            ranges['7-9'] += 1
        elif level <= 12:
            ranges['10-12'] += 1
        else:
            ranges['13+'] += 1
    
    return ranges

def update_user_ranking(user: Dict, leaderboard_types: List[str]):
    """
    특정 리더보드 타입들에 사용자 순위 업데이트
    """
    try:
        user_id = user['userId']
        score = user.get('totalScore', 0)
        username = user.get('username', f'Player_{user_id[-6:]}')
        level = user.get('level', 1)
        accuracy = user.get('stats', {}).get('accuracy', 0.0)
        
        for lb_type in leaderboard_types:
            # 기존 엔트리 삭제
            try:
                existing_response = leaderboard_table.query(
                    IndexName='userId-index',
                    KeyConditionExpression=Key('userId').eq(user_id),
                    FilterExpression=Attr('leaderboardType').eq(lb_type)
                )
                
                for item in existing_response.get('Items', []):
                    leaderboard_table.delete_item(
                        Key={
                            'leaderboardType': lb_type,
                            'score': item['score']
                        }
                    )
            except Exception as e:
                print(f"Error deleting existing ranking: {str(e)}")
            
            # 새 엔트리 추가
            leaderboard_table.put_item(
                Item={
                    'leaderboardType': lb_type,
                    'score': score,
                    'userId': user_id,
                    'username': username,
                    'level': level,
                    'accuracy': accuracy,
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }
            )
        
    except Exception as e:
        print(f"Error updating user ranking: {str(e)}")
        raise
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
