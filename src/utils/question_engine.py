"""
AWS Problem Solver Game - Question Engine
문제 출제, 선택, 난이도 조절을 담당하는 엔진
"""

import json
import random
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

class QuestionEngine:
    """
    문제 출제 엔진 클래스
    """
    
    def __init__(self):
        """
        문제 엔진 초기화
        """
        self.questions_db = self._load_questions_database()
        self.user_performance = {}
        self.question_stats = defaultdict(lambda: {'attempts': 0, 'correct': 0, 'avg_time': 0})
        
    def _load_questions_database(self) -> Dict:
        """
        모든 문제 데이터베이스 로드
        """
        questions_db = {}
        question_files = [
            'ec2_questions.json',
            's3_questions.json', 
            'rds_questions.json',
            'vpc_questions.json',
            'lambda_questions.json'
        ]
        
        base_path = os.path.join(os.path.dirname(__file__), '..', 'game_data', 'questions')
        
        for file_name in question_files:
            try:
                file_path = os.path.join(base_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    category = file_name.split('_')[0].upper()
                    questions_db[category] = data.get('questions', [])
            except FileNotFoundError:
                print(f"Warning: {file_name} not found")
                questions_db[category] = []
        
        return questions_db
    
    def get_random_question(self, filters: Dict = None) -> Optional[Dict]:
        """
        필터 조건에 맞는 랜덤 문제 반환
        
        Args:
            filters: 필터 조건 (category, difficulty, npc, tags 등)
            
        Returns:
            선택된 문제 또는 None
        """
        filtered_questions = self._filter_questions(filters or {})
        
        if not filtered_questions:
            return None
        
        # 가중치 기반 선택 (덜 출제된 문제 우선)
        selected_question = self._weighted_random_selection(filtered_questions)
        
        return self._prepare_question_for_client(selected_question)
    
    def get_adaptive_question(self, user_id: str, session_context: Dict = None) -> Optional[Dict]:
        """
        사용자 실력에 맞는 적응형 문제 선택
        
        Args:
            user_id: 사용자 ID
            session_context: 세션 컨텍스트 (NPC, 시나리오 등)
            
        Returns:
            적응형 선택된 문제
        """
        user_stats = self.user_performance.get(user_id, {})
        
        # 사용자 실력 분석
        difficulty_preference = self._analyze_user_difficulty_preference(user_stats)
        category_preference = self._analyze_user_category_preference(user_stats, session_context)
        
        # 필터 조건 구성
        filters = {
            'difficulty': difficulty_preference,
            'categories': category_preference,
            'exclude_recent': self._get_recent_questions(user_id),
            'user_weak_areas': self._identify_weak_areas(user_stats)
        }
        
        # 세션 컨텍스트 반영
        if session_context:
            if 'npc_id' in session_context:
                filters['npc'] = session_context['npc_id']
            if 'scenario_id' in session_context:
                filters['scenario_focus'] = session_context['scenario_id']
        
        return self.get_random_question(filters)
    
    def get_questions_by_scenario(self, scenario_id: str, phase: int = 1) -> List[Dict]:
        """
        시나리오별 문제 선택
        
        Args:
            scenario_id: 시나리오 ID
            phase: 시나리오 단계
            
        Returns:
            시나리오에 맞는 문제 리스트
        """
        scenario_mapping = {
            'startup_scaling': {
                1: ['ec2_001'],  # 트래픽 급증 대응
                2: ['ec2_004'],  # 비용 최적화
                3: ['s3_005']    # 글로벌 성능
            },
            'data_pipeline_optimization': {
                1: ['s3_002', 's3_004'],  # 데이터 저장 최적화
                2: ['lambda_002', 'lambda_003'],  # 실시간 처리
                3: ['lambda_003']  # 워크플로우 자동화
            },
            'security_hardening': {
                1: ['vpc_001', 'vpc_002'],  # 네트워크 보안
                2: ['s3_003', 'rds_004'],  # 데이터 보안
                3: ['lambda_004']  # 보안 자동화
            },
            'serverless_journey': {
                1: ['lambda_001'],  # 서버리스 API
                2: ['s3_001'],      # 정적 호스팅
                3: ['lambda_002'],  # 이벤트 처리
                4: ['rds_001']      # DB 현대화
            }
        }
        
        question_ids = scenario_mapping.get(scenario_id, {}).get(phase, [])
        questions = []
        
        for question_id in question_ids:
            question = self._find_question_by_id(question_id)
            if question:
                questions.append(self._prepare_question_for_client(question))
        
        return questions
    
    def get_questions_by_npc(self, npc_id: str, count: int = 5, user_level: int = 1) -> List[Dict]:
        """
        NPC별 맞춤 문제 선택
        
        Args:
            npc_id: NPC ID
            count: 문제 개수
            user_level: 사용자 레벨
            
        Returns:
            NPC에 맞는 문제 리스트
        """
        npc_preferences = {
            'alex_ceo': {
                'categories': ['EC2', 'S3', 'RDS'],
                'difficulties': ['easy', 'medium'],
                'focus_areas': ['cost-optimization', 'scaling', 'performance']
            },
            'sarah_analyst': {
                'categories': ['S3', 'LAMBDA'],
                'difficulties': ['medium', 'hard'],
                'focus_areas': ['data-processing', 'analytics', 'automation']
            },
            'mike_security': {
                'categories': ['VPC', 'S3', 'RDS'],
                'difficulties': ['medium', 'hard'],
                'focus_areas': ['security', 'compliance', 'access-control']
            },
            'jenny_developer': {
                'categories': ['LAMBDA', 'S3', 'RDS'],
                'difficulties': ['easy', 'medium', 'hard'],
                'focus_areas': ['serverless', 'api-development', 'automation']
            }
        }
        
        preferences = npc_preferences.get(npc_id, {})
        if not preferences:
            return []
        
        # 사용자 레벨에 따른 난이도 조정
        if user_level <= 3:
            difficulties = ['easy']
        elif user_level <= 6:
            difficulties = ['easy', 'medium']
        else:
            difficulties = preferences.get('difficulties', ['medium'])
        
        filters = {
            'categories': preferences.get('categories', []),
            'difficulties': difficulties,
            'npc': npc_id,
            'tags': preferences.get('focus_areas', [])
        }
        
        questions = []
        attempts = 0
        max_attempts = count * 3  # 무한 루프 방지
        
        while len(questions) < count and attempts < max_attempts:
            question = self.get_random_question(filters)
            if question and not any(q['questionId'] == question['questionId'] for q in questions):
                questions.append(question)
            attempts += 1
        
        return questions
    
    def validate_answer(self, question_id: str, selected_answer: str, user_id: str = None, 
                       time_spent: int = 0, hints_used: int = 0) -> Dict:
        """
        답안 검증 및 결과 반환
        
        Args:
            question_id: 문제 ID
            selected_answer: 선택한 답안
            user_id: 사용자 ID
            time_spent: 소요 시간 (초)
            hints_used: 사용한 힌트 수
            
        Returns:
            검증 결과
        """
        question = self._find_question_by_id(question_id)
        if not question:
            return {'error': '문제를 찾을 수 없습니다.'}
        
        # 정답 확인
        correct_answer = None
        for option in question.get('options', []):
            if option.get('isCorrect', False):
                correct_answer = option['id']
                break
        
        is_correct = selected_answer == correct_answer
        
        # 점수 계산
        score_result = self._calculate_score(question, is_correct, time_spent, hints_used)
        
        # 사용자 성과 업데이트
        if user_id:
            self._update_user_performance(user_id, question, is_correct, time_spent, hints_used, score_result)
        
        # 문제 통계 업데이트
        self._update_question_stats(question_id, is_correct, time_spent)
        
        result = {
            'questionId': question_id,
            'selectedAnswer': selected_answer,
            'correctAnswer': correct_answer,
            'isCorrect': is_correct,
            'explanation': question.get('explanation', ''),
            'score': score_result,
            'timeSpent': time_spent,
            'hintsUsed': hints_used,
            'difficulty': question.get('difficulty', 'medium'),
            'category': question.get('category', ''),
            'tags': question.get('tags', [])
        }
        
        # 추가 학습 자료 제안
        if not is_correct:
            result['learning_resources'] = self._get_learning_resources(question)
            result['similar_questions'] = self._get_similar_questions(question, limit=2)
        
        return result
    
    def get_question_statistics(self, question_id: str = None) -> Dict:
        """
        문제 통계 조회
        
        Args:
            question_id: 특정 문제 ID (None이면 전체 통계)
            
        Returns:
            문제 통계 정보
        """
        if question_id:
            stats = self.question_stats.get(question_id, {})
            return {
                'questionId': question_id,
                'attempts': stats.get('attempts', 0),
                'correctAnswers': stats.get('correct', 0),
                'accuracy': stats.get('correct', 0) / max(stats.get('attempts', 1), 1) * 100,
                'averageTime': stats.get('avg_time', 0)
            }
        else:
            # 전체 통계
            total_attempts = sum(stats['attempts'] for stats in self.question_stats.values())
            total_correct = sum(stats['correct'] for stats in self.question_stats.values())
            
            return {
                'totalQuestions': len(self.question_stats),
                'totalAttempts': total_attempts,
                'totalCorrect': total_correct,
                'overallAccuracy': total_correct / max(total_attempts, 1) * 100,
                'questionBreakdown': {qid: self.get_question_statistics(qid) 
                                    for qid in self.question_stats.keys()}
            }
    
    def _filter_questions(self, filters: Dict) -> List[Dict]:
        """
        필터 조건에 맞는 문제들 반환
        """
        all_questions = []
        
        # 모든 카테고리의 문제 수집
        for category, questions in self.questions_db.items():
            all_questions.extend(questions)
        
        filtered = all_questions
        
        # 카테고리 필터
        if 'category' in filters:
            filtered = [q for q in filtered if q.get('category') == filters['category']]
        elif 'categories' in filters:
            filtered = [q for q in filtered if q.get('category') in filters['categories']]
        
        # 난이도 필터
        if 'difficulty' in filters:
            if isinstance(filters['difficulty'], list):
                filtered = [q for q in filtered if q.get('difficulty') in filters['difficulty']]
            else:
                filtered = [q for q in filtered if q.get('difficulty') == filters['difficulty']]
        elif 'difficulties' in filters:
            filtered = [q for q in filtered if q.get('difficulty') in filters['difficulties']]
        
        # NPC 필터
        if 'npc' in filters:
            filtered = [q for q in filtered if q.get('npcCharacter') == filters['npc']]
        
        # 태그 필터
        if 'tags' in filters:
            filtered = [q for q in filtered if any(tag in q.get('tags', []) for tag in filters['tags'])]
        
        # 최근 문제 제외
        if 'exclude_recent' in filters:
            recent_ids = filters['exclude_recent']
            filtered = [q for q in filtered if q.get('questionId') not in recent_ids]
        
        # 활성 문제만
        filtered = [q for q in filtered if q.get('isActive', True)]
        
        return filtered
    
    def _weighted_random_selection(self, questions: List[Dict]) -> Dict:
        """
        가중치 기반 랜덤 선택 (덜 출제된 문제 우선)
        """
        if not questions:
            return None
        
        # 각 문제의 출제 횟수 기반 가중치 계산
        weights = []
        for question in questions:
            question_id = question.get('questionId')
            attempts = self.question_stats[question_id]['attempts']
            # 출제 횟수가 적을수록 높은 가중치
            weight = max(1, 10 - attempts)
            weights.append(weight)
        
        # 가중치 기반 랜덤 선택
        return random.choices(questions, weights=weights)[0]
    
    def _analyze_user_difficulty_preference(self, user_stats: Dict) -> List[str]:
        """
        사용자 실력에 맞는 난이도 분석
        """
        if not user_stats:
            return ['easy']
        
        accuracy = user_stats.get('overall_accuracy', 0)
        level = user_stats.get('level', 1)
        
        if accuracy >= 80 and level >= 5:
            return ['medium', 'hard']
        elif accuracy >= 60 and level >= 3:
            return ['easy', 'medium']
        else:
            return ['easy']
    
    def _analyze_user_category_preference(self, user_stats: Dict, session_context: Dict = None) -> List[str]:
        """
        사용자 선호 카테고리 분석
        """
        # 세션 컨텍스트 우선
        if session_context and 'preferred_categories' in session_context:
            return session_context['preferred_categories']
        
        # 사용자 통계 기반
        if user_stats and 'category_performance' in user_stats:
            # 성과가 좋은 카테고리와 약한 카테고리 균형
            strong_categories = [cat for cat, perf in user_stats['category_performance'].items() 
                               if perf.get('accuracy', 0) >= 70]
            weak_categories = [cat for cat, perf in user_stats['category_performance'].items() 
                             if perf.get('accuracy', 0) < 50]
            
            # 강한 분야 70%, 약한 분야 30% 비율로 선택
            preferred = strong_categories + weak_categories[:2]
            return preferred if preferred else ['EC2', 'S3']
        
        # 기본값
        return ['EC2', 'S3', 'RDS']
    
    def _get_recent_questions(self, user_id: str, limit: int = 5) -> List[str]:
        """
        최근 출제된 문제 ID 목록 반환
        """
        user_stats = self.user_performance.get(user_id, {})
        recent_questions = user_stats.get('recent_questions', [])
        return recent_questions[-limit:] if recent_questions else []
    
    def _identify_weak_areas(self, user_stats: Dict) -> List[str]:
        """
        사용자 약점 영역 식별
        """
        if not user_stats or 'category_performance' not in user_stats:
            return []
        
        weak_areas = []
        for category, performance in user_stats['category_performance'].items():
            if performance.get('accuracy', 0) < 60:
                weak_areas.append(category)
        
        return weak_areas
    
    def _find_question_by_id(self, question_id: str) -> Optional[Dict]:
        """
        문제 ID로 문제 찾기
        """
        for category, questions in self.questions_db.items():
            for question in questions:
                if question.get('questionId') == question_id:
                    return question
        return None
    
    def _prepare_question_for_client(self, question: Dict) -> Dict:
        """
        클라이언트용 문제 데이터 준비 (정답 정보 제외)
        """
        if not question:
            return None
        
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
    
    def _calculate_score(self, question: Dict, is_correct: bool, time_spent: int, hints_used: int) -> Dict:
        """
        점수 계산
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
                'experience': 10,
                'bonus': 0,
                'breakdown': {'base': 0, 'difficulty': 0, 'time': 0, 'hint_penalty': 0}
            }
        
        # 기본 점수 계산
        difficulty = question.get('difficulty', 'medium')
        difficulty_points = int(base_points * difficulty_multiplier.get(difficulty, 1.0))
        
        # 시간 보너스
        estimated_time = question.get('estimatedTime', 60)
        time_bonus = 0
        if time_spent < estimated_time * 0.5:
            time_bonus = int(difficulty_points * 0.3)
        elif time_spent < estimated_time * 0.8:
            time_bonus = int(difficulty_points * 0.1)
        
        # 힌트 페널티
        hint_penalty = hints_used * int(difficulty_points * 0.1)
        
        # 최종 점수
        total_points = max(0, difficulty_points + time_bonus - hint_penalty)
        experience = int(total_points * 0.5) + 20
        
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
    
    def _update_user_performance(self, user_id: str, question: Dict, is_correct: bool, 
                                time_spent: int, hints_used: int, score_result: Dict):
        """
        사용자 성과 업데이트
        """
        if user_id not in self.user_performance:
            self.user_performance[user_id] = {
                'total_questions': 0,
                'correct_answers': 0,
                'total_time': 0,
                'total_hints': 0,
                'category_performance': {},
                'recent_questions': [],
                'level': 1,
                'overall_accuracy': 0
            }
        
        user_stats = self.user_performance[user_id]
        category = question.get('category', 'UNKNOWN')
        
        # 전체 통계 업데이트
        user_stats['total_questions'] += 1
        if is_correct:
            user_stats['correct_answers'] += 1
        user_stats['total_time'] += time_spent
        user_stats['total_hints'] += hints_used
        user_stats['overall_accuracy'] = user_stats['correct_answers'] / user_stats['total_questions'] * 100
        
        # 카테고리별 성과 업데이트
        if category not in user_stats['category_performance']:
            user_stats['category_performance'][category] = {
                'attempts': 0, 'correct': 0, 'accuracy': 0, 'avg_time': 0
            }
        
        cat_perf = user_stats['category_performance'][category]
        cat_perf['attempts'] += 1
        if is_correct:
            cat_perf['correct'] += 1
        cat_perf['accuracy'] = cat_perf['correct'] / cat_perf['attempts'] * 100
        cat_perf['avg_time'] = (cat_perf.get('avg_time', 0) * (cat_perf['attempts'] - 1) + time_spent) / cat_perf['attempts']
        
        # 최근 문제 기록
        user_stats['recent_questions'].append(question['questionId'])
        if len(user_stats['recent_questions']) > 10:
            user_stats['recent_questions'] = user_stats['recent_questions'][-10:]
    
    def _update_question_stats(self, question_id: str, is_correct: bool, time_spent: int):
        """
        문제 통계 업데이트
        """
        stats = self.question_stats[question_id]
        stats['attempts'] += 1
        if is_correct:
            stats['correct'] += 1
        
        # 평균 시간 업데이트
        current_avg = stats.get('avg_time', 0)
        stats['avg_time'] = (current_avg * (stats['attempts'] - 1) + time_spent) / stats['attempts']
    
    def _get_learning_resources(self, question: Dict) -> List[Dict]:
        """
        학습 자료 추천
        """
        category = question.get('category', '')
        tags = question.get('tags', [])
        
        resources = []
        
        # AWS 공식 문서 링크
        aws_docs = {
            'EC2': 'https://docs.aws.amazon.com/ec2/',
            'S3': 'https://docs.aws.amazon.com/s3/',
            'RDS': 'https://docs.aws.amazon.com/rds/',
            'VPC': 'https://docs.aws.amazon.com/vpc/',
            'LAMBDA': 'https://docs.aws.amazon.com/lambda/'
        }
        
        if category in aws_docs:
            resources.append({
                'type': 'documentation',
                'title': f'AWS {category} 공식 문서',
                'url': aws_docs[category],
                'description': f'{category} 서비스에 대한 상세한 공식 문서'
            })
        
        # 태그 기반 추가 자료
        for tag in tags:
            if 'auto-scaling' in tag:
                resources.append({
                    'type': 'tutorial',
                    'title': 'Auto Scaling 실습 가이드',
                    'url': '#',
                    'description': 'Auto Scaling 설정 및 운영 방법'
                })
        
        return resources[:3]  # 최대 3개
    
    def _get_similar_questions(self, question: Dict, limit: int = 2) -> List[Dict]:
        """
        유사한 문제 추천
        """
        category = question.get('category')
        difficulty = question.get('difficulty')
        tags = set(question.get('tags', []))
        current_id = question.get('questionId')
        
        similar_questions = []
        
        for cat_questions in self.questions_db.values():
            for q in cat_questions:
                if (q.get('questionId') != current_id and 
                    q.get('category') == category and
                    q.get('difficulty') == difficulty):
                    
                    # 태그 유사도 계산
                    q_tags = set(q.get('tags', []))
                    similarity = len(tags.intersection(q_tags)) / len(tags.union(q_tags)) if tags.union(q_tags) else 0
                    
                    if similarity > 0.3:  # 30% 이상 유사
                        similar_questions.append({
                            'questionId': q['questionId'],
                            'title': q['scenario']['title'],
                            'similarity': similarity
                        })
        
        # 유사도 순으로 정렬하여 상위 문제 반환
        similar_questions.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_questions[:limit]

# 전역 인스턴스
question_engine = QuestionEngine()

# 편의 함수들
def get_random_question(filters: Dict = None) -> Optional[Dict]:
    """랜덤 문제 선택 편의 함수"""
    return question_engine.get_random_question(filters)

def get_adaptive_question(user_id: str, session_context: Dict = None) -> Optional[Dict]:
    """적응형 문제 선택 편의 함수"""
    return question_engine.get_adaptive_question(user_id, session_context)

def validate_answer(question_id: str, selected_answer: str, user_id: str = None, 
                   time_spent: int = 0, hints_used: int = 0) -> Dict:
    """답안 검증 편의 함수"""
    return question_engine.validate_answer(question_id, selected_answer, user_id, time_spent, hints_used)
