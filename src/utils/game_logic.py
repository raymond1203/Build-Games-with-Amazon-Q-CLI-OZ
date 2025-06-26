"""
AWS Problem Solver Game - Game Logic Utilities
게임 로직 관련 유틸리티 함수들
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .q_cli_integration import q_cli, generate_question_hint

class GameSession:
    """
    게임 세션 관리 클래스
    """
    
    def __init__(self, user_id: str, npc_character: str = None):
        """
        게임 세션 초기화
        
        Args:
            user_id: 사용자 ID
            npc_character: NPC 캐릭터 (선택사항)
        """
        self.session_id = self._generate_session_id()
        self.user_id = user_id
        self.npc_character = npc_character or self._select_random_npc()
        self.questions = []
        self.current_question_index = 0
        self.start_time = datetime.utcnow()
        self.status = 'active'
        self.hints_used = 0
        self.total_score = 0
    
    def _generate_session_id(self) -> str:
        """
        세션 ID 생성
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        random_suffix = random.randint(1000, 9999)
        return f"session_{timestamp}_{random_suffix}"
    
    def _select_random_npc(self) -> str:
        """
        랜덤 NPC 선택
        """
        npcs = ['alex_ceo', 'sarah_analyst', 'mike_security', 'jenny_developer']
        return random.choice(npcs)
    
    def add_question(self, question_data: Dict):
        """
        세션에 문제 추가
        """
        self.questions.append({
            'questionId': question_data['questionId'],
            'startTime': datetime.utcnow().isoformat() + 'Z',
            'selectedAnswer': None,
            'isCorrect': None,
            'timeSpent': 0,
            'hintsUsed': 0,
            'points': 0
        })
    
    def submit_answer(self, answer: str, time_spent: int, hints_used: int = 0) -> Dict:
        """
        답안 제출
        """
        if self.current_question_index >= len(self.questions):
            raise ValueError("No active question to answer")
        
        current_q = self.questions[self.current_question_index]
        current_q['selectedAnswer'] = answer
        current_q['timeSpent'] = time_spent
        current_q['hintsUsed'] = hints_used
        current_q['endTime'] = datetime.utcnow().isoformat() + 'Z'
        
        self.hints_used += hints_used
        self.current_question_index += 1
        
        return current_q
    
    def get_session_summary(self) -> Dict:
        """
        세션 요약 정보 반환
        """
        completed_questions = [q for q in self.questions if q.get('selectedAnswer') is not None]
        correct_answers = [q for q in completed_questions if q.get('isCorrect', False)]
        
        total_time = sum(q.get('timeSpent', 0) for q in completed_questions)
        
        return {
            'sessionId': self.session_id,
            'userId': self.user_id,
            'npcCharacter': self.npc_character,
            'totalQuestions': len(completed_questions),
            'correctAnswers': len(correct_answers),
            'accuracy': round(len(correct_answers) / len(completed_questions) * 100, 1) if completed_questions else 0,
            'totalTime': total_time,
            'totalPoints': self.total_score,
            'hintsUsed': self.hints_used,
            'status': self.status
        }

class NPCManager:
    """
    NPC 캐릭터 관리 클래스
    """
    
    def __init__(self):
        self.npcs = self._load_npc_data()
    
    def _load_npc_data(self) -> Dict:
        """
        NPC 데이터 로드
        """
        return {
            'alex_ceo': {
                'name': 'Alex',
                'title': '스타트업 CEO',
                'personality': 'energetic',
                'expertise': ['EC2', 'Auto Scaling', 'Load Balancer'],
                'greeting': "안녕하세요! 저는 스타트업을 운영하는 Alex입니다. 우리 서비스가 갑자기 인기를 끌면서 기술적인 문제들이 생겼어요. 도움을 주실 수 있나요?",
                'problem_style': 'urgent',
                'difficulty_preference': ['easy', 'medium']
            },
            'sarah_analyst': {
                'name': 'Sarah',
                'title': '데이터 분석가',
                'personality': 'analytical',
                'expertise': ['S3', 'Athena', 'Redshift', 'EMR'],
                'greeting': "안녕하세요, 데이터 분석가 Sarah입니다. 대용량 데이터 처리와 분석에 관련된 AWS 솔루션에 대해 궁금한 점이 있어요.",
                'problem_style': 'data_focused',
                'difficulty_preference': ['medium', 'hard']
            },
            'mike_security': {
                'name': 'Mike',
                'title': '보안 담당자',
                'personality': 'cautious',
                'expertise': ['IAM', 'VPC', 'Security Groups', 'KMS'],
                'greeting': "보안 담당자 Mike입니다. 클라우드 보안을 강화하고 싶은데, AWS의 보안 서비스들에 대해 조언을 구하고 싶습니다.",
                'problem_style': 'security_focused',
                'difficulty_preference': ['medium', 'hard']
            },
            'jenny_developer': {
                'name': 'Jenny',
                'title': '풀스택 개발자',
                'personality': 'curious',
                'expertise': ['Lambda', 'API Gateway', 'DynamoDB', 'CloudWatch'],
                'greeting': "개발자 Jenny입니다! 서버리스 아키텍처로 애플리케이션을 만들고 싶은데, 어떤 AWS 서비스들을 사용해야 할지 고민이에요.",
                'problem_style': 'development_focused',
                'difficulty_preference': ['easy', 'medium', 'hard']
            }
        }
    
    def get_npc_info(self, npc_id: str) -> Optional[Dict]:
        """
        NPC 정보 반환
        """
        return self.npcs.get(npc_id)
    
    def get_npc_greeting(self, npc_id: str) -> str:
        """
        NPC 인사말 반환
        """
        npc = self.npcs.get(npc_id)
        if npc:
            return npc['greeting']
        return "안녕하세요! AWS 문제를 함께 해결해보아요."
    
    def get_npc_response(self, npc_id: str, context: str) -> str:
        """
        NPC 응답 생성 (Amazon Q CLI 활용)
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            return "죄송합니다. 지금은 응답할 수 없어요."
        
        # NPC 성격에 맞는 응답 생성
        prompt = f"""
        당신은 {npc['title']} {npc['name']}입니다. 
        성격: {npc['personality']}
        전문분야: {', '.join(npc['expertise'])}
        
        다음 상황에 대해 {npc['name']}의 성격과 전문성을 반영하여 응답해주세요:
        {context}
        
        응답은 친근하고 도움이 되는 톤으로, 해당 캐릭터의 관점에서 작성해주세요.
        """
        
        response = q_cli.ask_question(prompt)
        return response or f"{npc['name']}: 죄송해요, 지금은 생각이 잘 안 나네요. 다른 질문을 해보시겠어요?"

class QuestionSelector:
    """
    문제 선택 로직 클래스
    """
    
    @staticmethod
    def select_questions_for_npc(npc_id: str, count: int = 5) -> List[Dict]:
        """
        NPC에 맞는 문제들 선택
        """
        npc_manager = NPCManager()
        npc_info = npc_manager.get_npc_info(npc_id)
        
        if not npc_info:
            return []
        
        # NPC의 전문분야와 선호 난이도에 맞는 문제 필터링 로직
        # 실제 구현에서는 DynamoDB에서 쿼리
        criteria = {
            'categories': npc_info['expertise'],
            'difficulties': npc_info['difficulty_preference'],
            'limit': count
        }
        
        return criteria  # 실제로는 DynamoDB 쿼리 결과 반환
    
    @staticmethod
    def select_adaptive_question(user_stats: Dict) -> Dict:
        """
        사용자 실력에 맞는 적응형 문제 선택
        """
        accuracy = user_stats.get('accuracy', 0)
        level = user_stats.get('level', 1)
        
        # 정답률에 따른 난이도 조절
        if accuracy >= 80:
            preferred_difficulty = 'hard'
        elif accuracy >= 60:
            preferred_difficulty = 'medium'
        else:
            preferred_difficulty = 'easy'
        
        # 레벨에 따른 카테고리 추천
        if level <= 3:
            preferred_categories = ['EC2', 'S3']
        elif level <= 6:
            preferred_categories = ['EC2', 'S3', 'RDS', 'VPC']
        else:
            preferred_categories = ['EC2', 'S3', 'RDS', 'VPC', 'Lambda', 'IAM']
        
        return {
            'difficulty': preferred_difficulty,
            'categories': preferred_categories
        }

class HintSystem:
    """
    힌트 시스템 클래스
    """
    
    @staticmethod
    def get_progressive_hint(question_data: Dict, hint_level: int, user_context: Dict = None) -> Dict:
        """
        단계적 힌트 제공
        """
        # 기본 힌트 (문제에 미리 정의된 힌트)
        predefined_hints = question_data.get('hints', [])
        
        if hint_level <= len(predefined_hints):
            hint_text = predefined_hints[hint_level - 1]
            source = 'predefined'
        else:
            # Amazon Q CLI를 통한 동적 힌트 생성
            hint_text = generate_question_hint(question_data, hint_level)
            source = 'ai_generated'
        
        # 힌트 사용에 따른 점수 페널티 계산
        base_points = question_data.get('points', 100)
        penalty = int(base_points * 0.1 * hint_level)  # 힌트 레벨당 10% 페널티
        
        return {
            'hint': hint_text or "죄송해요, 지금은 힌트를 제공할 수 없어요.",
            'hintLevel': hint_level,
            'source': source,
            'pointsPenalty': penalty,
            'remainingPoints': max(0, base_points - penalty)
        }
    
    @staticmethod
    def should_offer_hint(user_stats: Dict, time_spent: int, question_difficulty: str) -> bool:
        """
        힌트 제공 여부 결정
        """
        # 사용자 레벨이 낮거나 정답률이 낮으면 힌트 제안
        level = user_stats.get('level', 1)
        accuracy = user_stats.get('accuracy', 0)
        
        # 시간이 오래 걸리면 힌트 제안
        difficulty_time_thresholds = {
            'easy': 45,
            'medium': 60,
            'hard': 90
        }
        
        time_threshold = difficulty_time_thresholds.get(question_difficulty, 60)
        
        return (
            level <= 3 or 
            accuracy < 60 or 
            time_spent > time_threshold
        )

# 전역 인스턴스들
npc_manager = NPCManager()
question_selector = QuestionSelector()
hint_system = HintSystem()

# 편의 함수들
def create_game_session(user_id: str, npc_character: str = None) -> GameSession:
    """
    게임 세션 생성
    """
    return GameSession(user_id, npc_character)

def get_npc_dialogue(npc_id: str, context: str = '') -> str:
    """
    NPC 대화 생성
    """
    return npc_manager.get_npc_response(npc_id, context)

def select_next_question(user_stats: Dict, npc_id: str = None) -> Dict:
    """
    다음 문제 선택
    """
    if npc_id:
        # NPC 기반 문제 선택
        return question_selector.select_questions_for_npc(npc_id, 1)
    else:
        # 적응형 문제 선택
        return question_selector.select_adaptive_question(user_stats)

def get_smart_hint(question_data: Dict, hint_level: int, user_context: Dict = None) -> Dict:
    """
    스마트 힌트 제공
    """
    return hint_system.get_progressive_hint(question_data, hint_level, user_context)
