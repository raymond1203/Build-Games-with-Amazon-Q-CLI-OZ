"""
AWS Problem Solver Game - Difficulty Adapter
사용자 실력에 따른 동적 난이도 조절 시스템
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque

class DifficultyAdapter:
    """
    난이도 적응 시스템 클래스
    """
    
    def __init__(self):
        """
        난이도 어댑터 초기화
        """
        self.user_profiles = {}
        self.difficulty_thresholds = {
            'easy': {'min_accuracy': 0, 'max_accuracy': 70},
            'medium': {'min_accuracy': 60, 'max_accuracy': 85},
            'hard': {'min_accuracy': 80, 'max_accuracy': 100}
        }
        self.adaptation_history = {}
    
    def analyze_user_performance(self, user_id: str, recent_results: List[Dict]) -> Dict:
        """
        사용자 성과 분석
        
        Args:
            user_id: 사용자 ID
            recent_results: 최근 문제 결과 리스트
            
        Returns:
            성과 분석 결과
        """
        if not recent_results:
            return self._get_default_analysis()
        
        # 기본 통계 계산
        total_questions = len(recent_results)
        correct_answers = sum(1 for result in recent_results if result.get('is_correct', False))
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # 시간 분석
        avg_time = sum(result.get('time_spent', 0) for result in recent_results) / total_questions
        time_efficiency = self._calculate_time_efficiency(recent_results)
        
        # 난이도별 성과 분석
        difficulty_performance = self._analyze_difficulty_performance(recent_results)
        
        # 카테고리별 성과 분석
        category_performance = self._analyze_category_performance(recent_results)
        
        # 학습 곡선 분석
        learning_trend = self._analyze_learning_trend(recent_results)
        
        # 힌트 사용 패턴 분석
        hint_usage = self._analyze_hint_usage(recent_results)
        
        analysis = {
            'user_id': user_id,
            'analysis_date': datetime.now().isoformat(),
            'basic_stats': {
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'accuracy': accuracy,
                'average_time': avg_time,
                'time_efficiency': time_efficiency
            },
            'difficulty_performance': difficulty_performance,
            'category_performance': category_performance,
            'learning_trend': learning_trend,
            'hint_usage': hint_usage,
            'skill_level': self._determine_skill_level(accuracy, difficulty_performance),
            'confidence_score': self._calculate_confidence_score(recent_results),
            'improvement_areas': self._identify_improvement_areas(category_performance, difficulty_performance)
        }
        
        # 사용자 프로필 업데이트
        self.user_profiles[user_id] = analysis
        
        return analysis
    
    def recommend_difficulty(self, user_id: str, category: str = None, context: Dict = None) -> Dict:
        """
        사용자에게 적합한 난이도 추천
        
        Args:
            user_id: 사용자 ID
            category: 특정 카테고리 (선택사항)
            context: 추가 컨텍스트 (NPC, 시나리오 등)
            
        Returns:
            난이도 추천 결과
        """
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            return self._get_default_difficulty_recommendation()
        
        # 기본 난이도 결정
        base_difficulty = self._determine_base_difficulty(user_profile)
        
        # 카테고리별 조정
        if category:
            category_adjustment = self._get_category_difficulty_adjustment(user_profile, category)
            adjusted_difficulty = self._adjust_difficulty(base_difficulty, category_adjustment)
        else:
            adjusted_difficulty = base_difficulty
        
        # 컨텍스트 기반 조정
        if context:
            context_adjustment = self._get_context_difficulty_adjustment(user_profile, context)
            final_difficulty = self._adjust_difficulty(adjusted_difficulty, context_adjustment)
        else:
            final_difficulty = adjusted_difficulty
        
        # 학습 목표 기반 미세 조정
        learning_adjustment = self._get_learning_goal_adjustment(user_profile)
        final_difficulty = self._adjust_difficulty(final_difficulty, learning_adjustment)
        
        recommendation = {
            'recommended_difficulty': final_difficulty,
            'confidence': self._calculate_recommendation_confidence(user_profile, final_difficulty),
            'reasoning': self._generate_difficulty_reasoning(user_profile, base_difficulty, final_difficulty),
            'alternative_difficulties': self._get_alternative_difficulties(final_difficulty),
            'expected_success_rate': self._predict_success_rate(user_profile, final_difficulty, category)
        }
        
        # 추천 히스토리 기록
        self._record_difficulty_recommendation(user_id, recommendation)
        
        return recommendation
    
    def adapt_question_pool(self, user_id: str, available_questions: List[Dict]) -> List[Dict]:
        """
        사용자에게 맞는 문제 풀 조정
        
        Args:
            user_id: 사용자 ID
            available_questions: 사용 가능한 문제 리스트
            
        Returns:
            조정된 문제 리스트 (우선순위 순)
        """
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            return available_questions
        
        scored_questions = []
        
        for question in available_questions:
            score = self._calculate_question_suitability_score(user_profile, question)
            scored_questions.append({
                'question': question,
                'suitability_score': score,
                'predicted_difficulty': self._predict_question_difficulty_for_user(user_profile, question),
                'learning_value': self._calculate_learning_value(user_profile, question)
            })
        
        # 적합성 점수 순으로 정렬
        scored_questions.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return [item['question'] for item in scored_questions]
    
    def provide_adaptive_feedback(self, user_id: str, question_result: Dict) -> Dict:
        """
        적응형 피드백 제공
        
        Args:
            user_id: 사용자 ID
            question_result: 문제 결과
            
        Returns:
            맞춤형 피드백
        """
        user_profile = self.user_profiles.get(user_id)
        if not user_profile:
            return self._get_default_feedback(question_result)
        
        is_correct = question_result.get('is_correct', False)
        difficulty = question_result.get('difficulty', 'medium')
        category = question_result.get('category', '')
        time_spent = question_result.get('time_spent', 0)
        hints_used = question_result.get('hints_used', 0)
        
        # 성과 평가
        performance_evaluation = self._evaluate_performance(user_profile, question_result)
        
        # 피드백 타입 결정
        feedback_type = self._determine_feedback_type(performance_evaluation, user_profile)
        
        # 맞춤형 메시지 생성
        feedback_message = self._generate_adaptive_feedback_message(
            feedback_type, performance_evaluation, user_profile
        )
        
        # 다음 단계 추천
        next_steps = self._recommend_next_steps(user_profile, question_result)
        
        # 격려 또는 도전 메시지
        motivational_message = self._generate_motivational_message(user_profile, performance_evaluation)
        
        return {
            'feedback_type': feedback_type,
            'main_message': feedback_message,
            'motivational_message': motivational_message,
            'performance_evaluation': performance_evaluation,
            'next_steps': next_steps,
            'difficulty_adjustment': self._suggest_difficulty_adjustment(user_profile, question_result),
            'learning_tips': self._provide_learning_tips(user_profile, question_result)
        }
    
    def _get_default_analysis(self) -> Dict:
        """기본 분석 결과 반환"""
        return {
            'basic_stats': {'accuracy': 0, 'total_questions': 0},
            'skill_level': 'beginner',
            'confidence_score': 0.5,
            'improvement_areas': ['기본 개념 학습']
        }
    
    def _calculate_time_efficiency(self, results: List[Dict]) -> float:
        """시간 효율성 계산"""
        if not results:
            return 0.5
        
        efficiency_scores = []
        for result in results:
            estimated_time = result.get('estimated_time', 60)
            actual_time = result.get('time_spent', 60)
            is_correct = result.get('is_correct', False)
            
            if is_correct:
                # 정답이면서 빠르게 푼 경우 높은 점수
                efficiency = min(1.0, estimated_time / max(actual_time, 1))
            else:
                # 틀렸으면 시간과 관계없이 낮은 점수
                efficiency = 0.2
            
            efficiency_scores.append(efficiency)
        
        return sum(efficiency_scores) / len(efficiency_scores)
    
    def _analyze_difficulty_performance(self, results: List[Dict]) -> Dict:
        """난이도별 성과 분석"""
        difficulty_stats = {'easy': [], 'medium': [], 'hard': []}
        
        for result in results:
            difficulty = result.get('difficulty', 'medium')
            if difficulty in difficulty_stats:
                difficulty_stats[difficulty].append(result.get('is_correct', False))
        
        performance = {}
        for difficulty, correct_list in difficulty_stats.items():
            if correct_list:
                accuracy = sum(correct_list) / len(correct_list) * 100
                performance[difficulty] = {
                    'accuracy': accuracy,
                    'attempts': len(correct_list),
                    'trend': self._calculate_trend(correct_list)
                }
            else:
                performance[difficulty] = {'accuracy': 0, 'attempts': 0, 'trend': 'no_data'}
        
        return performance
    
    def _analyze_category_performance(self, results: List[Dict]) -> Dict:
        """카테고리별 성과 분석"""
        category_stats = {}
        
        for result in results:
            category = result.get('category', 'UNKNOWN')
            if category not in category_stats:
                category_stats[category] = []
            category_stats[category].append(result.get('is_correct', False))
        
        performance = {}
        for category, correct_list in category_stats.items():
            if correct_list:
                accuracy = sum(correct_list) / len(correct_list) * 100
                performance[category] = {
                    'accuracy': accuracy,
                    'attempts': len(correct_list),
                    'strength_level': self._categorize_strength(accuracy)
                }
        
        return performance
    
    def _analyze_learning_trend(self, results: List[Dict]) -> Dict:
        """학습 곡선 분석"""
        if len(results) < 3:
            return {'trend': 'insufficient_data', 'slope': 0}
        
        # 최근 결과들을 시간순으로 정렬
        sorted_results = sorted(results, key=lambda x: x.get('timestamp', ''))
        
        # 이동 평균을 사용한 트렌드 계산
        window_size = min(5, len(sorted_results) // 2)
        moving_averages = []
        
        for i in range(len(sorted_results) - window_size + 1):
            window = sorted_results[i:i + window_size]
            avg_accuracy = sum(r.get('is_correct', False) for r in window) / window_size
            moving_averages.append(avg_accuracy)
        
        # 트렌드 기울기 계산
        if len(moving_averages) >= 2:
            slope = (moving_averages[-1] - moving_averages[0]) / len(moving_averages)
            
            if slope > 0.1:
                trend = 'improving'
            elif slope < -0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
            slope = 0
        
        return {
            'trend': trend,
            'slope': slope,
            'recent_performance': moving_averages[-3:] if len(moving_averages) >= 3 else moving_averages
        }
    
    def _analyze_hint_usage(self, results: List[Dict]) -> Dict:
        """힌트 사용 패턴 분석"""
        total_hints = sum(result.get('hints_used', 0) for result in results)
        total_questions = len(results)
        
        if total_questions == 0:
            return {'avg_hints_per_question': 0, 'hint_dependency': 'low'}
        
        avg_hints = total_hints / total_questions
        
        # 힌트 의존도 분류
        if avg_hints >= 2:
            dependency = 'high'
        elif avg_hints >= 1:
            dependency = 'medium'
        else:
            dependency = 'low'
        
        # 힌트 사용과 정답률 상관관계
        hint_effectiveness = self._calculate_hint_effectiveness(results)
        
        return {
            'avg_hints_per_question': avg_hints,
            'hint_dependency': dependency,
            'hint_effectiveness': hint_effectiveness,
            'total_hints_used': total_hints
        }
    
    def _determine_skill_level(self, accuracy: float, difficulty_performance: Dict) -> str:
        """스킬 레벨 결정"""
        if accuracy >= 85 and difficulty_performance.get('hard', {}).get('accuracy', 0) >= 70:
            return 'expert'
        elif accuracy >= 75 and difficulty_performance.get('medium', {}).get('accuracy', 0) >= 70:
            return 'advanced'
        elif accuracy >= 60 and difficulty_performance.get('easy', {}).get('accuracy', 0) >= 70:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _calculate_confidence_score(self, results: List[Dict]) -> float:
        """자신감 점수 계산"""
        if not results:
            return 0.5
        
        # 최근 성과의 일관성 측정
        recent_results = results[-10:]  # 최근 10개 문제
        correct_answers = [r.get('is_correct', False) for r in recent_results]
        
        if not correct_answers:
            return 0.5
        
        # 정답률
        accuracy = sum(correct_answers) / len(correct_answers)
        
        # 일관성 (표준편차의 역수)
        if len(correct_answers) > 1:
            variance = sum((x - accuracy) ** 2 for x in correct_answers) / len(correct_answers)
            consistency = 1 / (1 + variance)
        else:
            consistency = 0.5
        
        # 시간 안정성
        time_stability = self._calculate_time_stability(recent_results)
        
        # 종합 자신감 점수
        confidence = (accuracy * 0.5 + consistency * 0.3 + time_stability * 0.2)
        return min(1.0, max(0.0, confidence))
    
    def _identify_improvement_areas(self, category_performance: Dict, difficulty_performance: Dict) -> List[str]:
        """개선 영역 식별"""
        improvement_areas = []
        
        # 카테고리별 약점 식별
        for category, perf in category_performance.items():
            if perf.get('accuracy', 0) < 60:
                improvement_areas.append(f"{category} 기본 개념")
        
        # 난이도별 약점 식별
        for difficulty, perf in difficulty_performance.items():
            if perf.get('accuracy', 0) < 50:
                improvement_areas.append(f"{difficulty} 난이도 문제 해결")
        
        # 기본 개선 영역
        if not improvement_areas:
            improvement_areas = ["전반적인 문제 해결 능력", "시간 관리"]
        
        return improvement_areas[:3]  # 최대 3개
    
    def _determine_base_difficulty(self, user_profile: Dict) -> str:
        """기본 난이도 결정"""
        skill_level = user_profile.get('skill_level', 'beginner')
        accuracy = user_profile.get('basic_stats', {}).get('accuracy', 0)
        
        if skill_level == 'expert' or accuracy >= 85:
            return 'hard'
        elif skill_level == 'advanced' or accuracy >= 70:
            return 'medium'
        else:
            return 'easy'
    
    def _get_category_difficulty_adjustment(self, user_profile: Dict, category: str) -> int:
        """카테고리별 난이도 조정값 반환 (-1, 0, 1)"""
        category_perf = user_profile.get('category_performance', {}).get(category, {})
        accuracy = category_perf.get('accuracy', 50)
        
        if accuracy >= 80:
            return 1  # 난이도 상승
        elif accuracy <= 40:
            return -1  # 난이도 하락
        else:
            return 0  # 유지
    
    def _adjust_difficulty(self, current_difficulty: str, adjustment: int) -> str:
        """난이도 조정"""
        difficulties = ['easy', 'medium', 'hard']
        current_index = difficulties.index(current_difficulty)
        new_index = max(0, min(len(difficulties) - 1, current_index + adjustment))
        return difficulties[new_index]
    
    def _calculate_trend(self, correct_list: List[bool]) -> str:
        """트렌드 계산"""
        if len(correct_list) < 3:
            return 'insufficient_data'
        
        recent = correct_list[-3:]
        earlier = correct_list[:-3] if len(correct_list) > 3 else correct_list[:3]
        
        recent_avg = sum(recent) / len(recent)
        earlier_avg = sum(earlier) / len(earlier)
        
        if recent_avg > earlier_avg + 0.2:
            return 'improving'
        elif recent_avg < earlier_avg - 0.2:
            return 'declining'
        else:
            return 'stable'
    
    def _categorize_strength(self, accuracy: float) -> str:
        """강점 수준 분류"""
        if accuracy >= 80:
            return 'strong'
        elif accuracy >= 60:
            return 'moderate'
        else:
            return 'weak'
    
    def _calculate_hint_effectiveness(self, results: List[Dict]) -> float:
        """힌트 효과성 계산"""
        hint_results = [r for r in results if r.get('hints_used', 0) > 0]
        no_hint_results = [r for r in results if r.get('hints_used', 0) == 0]
        
        if not hint_results or not no_hint_results:
            return 0.5
        
        hint_accuracy = sum(r.get('is_correct', False) for r in hint_results) / len(hint_results)
        no_hint_accuracy = sum(r.get('is_correct', False) for r in no_hint_results) / len(no_hint_results)
        
        # 힌트 사용 시 정답률 향상도
        effectiveness = hint_accuracy - no_hint_accuracy
        return max(0.0, min(1.0, effectiveness + 0.5))  # 0-1 범위로 정규화
    
    def _calculate_time_stability(self, results: List[Dict]) -> float:
        """시간 안정성 계산"""
        times = [r.get('time_spent', 60) for r in results if r.get('time_spent', 0) > 0]
        
        if len(times) < 2:
            return 0.5
        
        avg_time = sum(times) / len(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        
        # 변동성이 낮을수록 안정성 높음
        stability = 1 / (1 + variance / (avg_time ** 2))
        return min(1.0, max(0.0, stability))

# 전역 인스턴스
difficulty_adapter = DifficultyAdapter()

# 편의 함수들
def analyze_user_performance(user_id: str, recent_results: List[Dict]) -> Dict:
    """사용자 성과 분석 편의 함수"""
    return difficulty_adapter.analyze_user_performance(user_id, recent_results)

def recommend_difficulty(user_id: str, category: str = None, context: Dict = None) -> Dict:
    """난이도 추천 편의 함수"""
    return difficulty_adapter.recommend_difficulty(user_id, category, context)

def provide_adaptive_feedback(user_id: str, question_result: Dict) -> Dict:
    """적응형 피드백 편의 함수"""
    return difficulty_adapter.provide_adaptive_feedback(user_id, question_result)
