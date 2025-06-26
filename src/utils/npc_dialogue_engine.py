"""
AWS Problem Solver Game - NPC Dialogue Engine
NPC 캐릭터와의 대화 및 상호작용을 관리하는 엔진
"""

import json
import random
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .q_cli_integration import q_cli

class NPCDialogueEngine:
    """
    NPC 대화 엔진 클래스
    """
    
    def __init__(self):
        """
        대화 엔진 초기화
        """
        self.npc_data = self._load_npc_data()
        self.scenarios = self._load_scenarios()
        self.conversation_history = {}
        self.current_sessions = {}
    
    def _load_npc_data(self) -> Dict:
        """
        NPC 데이터 로드
        """
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'game_data', 'npcs', 'character_data.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 기본 NPC 데이터 반환
            return self._get_default_npc_data()
    
    def _load_scenarios(self) -> Dict:
        """
        시나리오 데이터 로드
        """
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'game_data', 'scenarios', 'business_cases.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"scenarios": {}}
    
    def start_conversation(self, user_id: str, npc_id: str, scenario_id: str = None) -> Dict:
        """
        NPC와의 대화 시작
        
        Args:
            user_id: 사용자 ID
            npc_id: NPC ID
            scenario_id: 시나리오 ID (선택사항)
            
        Returns:
            대화 시작 응답
        """
        if npc_id not in self.npc_data.get('npcs', {}):
            return self._create_error_response("존재하지 않는 NPC입니다.")
        
        npc = self.npc_data['npcs'][npc_id]
        
        # 대화 세션 초기화
        session_id = f"{user_id}_{npc_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_sessions[session_id] = {
            'user_id': user_id,
            'npc_id': npc_id,
            'scenario_id': scenario_id,
            'start_time': datetime.now().isoformat(),
            'phase': 1,
            'conversation_count': 0,
            'context': {}
        }
        
        # 인사말 생성
        greeting = self._generate_greeting(npc, scenario_id)
        
        # 대화 히스토리 초기화
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {}
        
        self.conversation_history[user_id][session_id] = [
            {
                'speaker': 'npc',
                'message': greeting,
                'timestamp': datetime.now().isoformat(),
                'type': 'greeting'
            }
        ]
        
        return {
            'session_id': session_id,
            'npc': {
                'id': npc_id,
                'name': npc['name'],
                'title': npc['title'],
                'avatar': npc.get('avatar', ''),
                'personality_type': npc['personality']['type']
            },
            'message': greeting,
            'scenario': self._get_scenario_info(scenario_id) if scenario_id else None,
            'options': self._get_conversation_options(npc, 'greeting'),
            'timestamp': datetime.now().isoformat()
        }
    
    def continue_conversation(self, session_id: str, user_message: str, context: Dict = None) -> Dict:
        """
        대화 계속하기
        
        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            context: 추가 컨텍스트 (문제 정답 여부 등)
            
        Returns:
            NPC 응답
        """
        if session_id not in self.current_sessions:
            return self._create_error_response("유효하지 않은 세션입니다.")
        
        session = self.current_sessions[session_id]
        npc = self.npc_data['npcs'][session['npc_id']]
        
        # 사용자 메시지 기록
        self._add_to_history(session['user_id'], session_id, 'user', user_message, context)
        
        # NPC 응답 생성
        response = self._generate_npc_response(npc, user_message, context, session)
        
        # NPC 응답 기록
        self._add_to_history(session['user_id'], session_id, 'npc', response['message'], {'type': response['type']})
        
        # 세션 업데이트
        session['conversation_count'] += 1
        if context:
            session['context'].update(context)
        
        return response
    
    def get_hint_response(self, session_id: str, question_data: Dict, hint_level: int) -> Dict:
        """
        힌트 요청에 대한 NPC 응답
        
        Args:
            session_id: 세션 ID
            question_data: 문제 데이터
            hint_level: 힌트 레벨
            
        Returns:
            힌트와 함께하는 NPC 응답
        """
        if session_id not in self.current_sessions:
            return self._create_error_response("유효하지 않은 세션입니다.")
        
        session = self.current_sessions[session_id]
        npc = self.npc_data['npcs'][session['npc_id']]
        
        # NPC 성격에 맞는 힌트 제공 방식 결정
        hint_style = self._get_hint_style(npc, hint_level)
        
        # 기본 힌트 또는 AI 생성 힌트
        if hint_level <= len(question_data.get('hints', [])):
            base_hint = question_data['hints'][hint_level - 1]
        else:
            base_hint = self._generate_ai_hint(question_data, hint_level, npc)
        
        # NPC 성격에 맞게 힌트 포장
        npc_hint_message = self._wrap_hint_with_personality(npc, base_hint, hint_style)
        
        return {
            'session_id': session_id,
            'message': npc_hint_message,
            'hint': base_hint,
            'hint_level': hint_level,
            'type': 'hint',
            'personality_style': hint_style,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_greeting(self, npc: Dict, scenario_id: str = None) -> str:
        """
        NPC 인사말 생성
        """
        base_greeting = npc['dialogue']['greeting']
        
        if scenario_id and scenario_id in self.scenarios.get('scenarios', {}):
            scenario = self.scenarios['scenarios'][scenario_id]
            scenario_context = f"\n\n{scenario['background_story']}"
            return base_greeting + scenario_context
        
        return base_greeting
    
    def _generate_npc_response(self, npc: Dict, user_message: str, context: Dict, session: Dict) -> Dict:
        """
        NPC 응답 생성
        """
        # 컨텍스트에 따른 응답 타입 결정
        if context and 'answer_result' in context:
            if context['answer_result']['is_correct']:
                response_type = 'correct_response'
                responses = npc['dialogue']['correct_response']
            else:
                response_type = 'incorrect_response'
                responses = npc['dialogue']['incorrect_response']
        elif 'hint' in user_message.lower() or 'help' in user_message.lower():
            response_type = 'hint_request'
            responses = npc['dialogue']['hint_request']
        else:
            response_type = 'general_response'
            responses = self._generate_contextual_response(npc, user_message, session)
        
        # 응답 선택 (랜덤 또는 컨텍스트 기반)
        if isinstance(responses, list):
            selected_response = random.choice(responses)
        else:
            selected_response = responses
        
        # AI 기반 응답 개선 (선택사항)
        enhanced_response = self._enhance_response_with_ai(npc, selected_response, user_message, context)
        
        return {
            'message': enhanced_response or selected_response,
            'type': response_type,
            'options': self._get_conversation_options(npc, response_type),
            'personality_indicators': self._get_personality_indicators(npc, response_type),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_contextual_response(self, npc: Dict, user_message: str, session: Dict) -> List[str]:
        """
        컨텍스트 기반 응답 생성
        """
        personality = npc['personality']['type']
        
        # 성격별 기본 응답 패턴
        if personality == 'energetic':
            return [
                "그렇군요! 빠르게 해결해봐야겠네요!",
                "좋은 아이디어네요! 바로 적용해볼까요?",
                "시간이 중요하니까 효율적인 방법을 찾아봅시다!"
            ]
        elif personality == 'analytical':
            return [
                "흥미로운 접근법이네요. 데이터를 좀 더 분석해볼까요?",
                "정확한 분석이 필요할 것 같습니다.",
                "체계적으로 접근해보는 게 좋겠어요."
            ]
        elif personality == 'cautious':
            return [
                "보안 측면에서 검토가 필요할 것 같습니다.",
                "안전한 방법인지 확인해봐야겠어요.",
                "규제 요구사항도 고려해야 합니다."
            ]
        elif personality == 'curious':
            return [
                "와! 새로운 방법이네요! 더 알고 싶어요!",
                "이런 접근법도 있었군요! 흥미로워요!",
                "배울 게 정말 많네요!"
            ]
        
        return ["네, 이해했습니다."]
    
    def _get_hint_style(self, npc: Dict, hint_level: int) -> str:
        """
        NPC 성격에 따른 힌트 제공 스타일 결정
        """
        personality = npc['personality']['type']
        
        if personality == 'energetic':
            return 'urgent' if hint_level <= 2 else 'direct'
        elif personality == 'analytical':
            return 'methodical'
        elif personality == 'cautious':
            return 'thorough'
        elif personality == 'curious':
            return 'encouraging'
        
        return 'neutral'
    
    def _wrap_hint_with_personality(self, npc: Dict, hint: str, style: str) -> str:
        """
        NPC 성격에 맞게 힌트 포장
        """
        name = npc['name']
        
        style_wrappers = {
            'urgent': f"{name}: 시간이 없어요! {hint} 빨리 해결해봅시다!",
            'direct': f"{name}: {hint} 이 방법이 가장 효과적일 거예요.",
            'methodical': f"{name}: 차근차근 생각해보면... {hint} 이런 접근이 좋을 것 같아요.",
            'thorough': f"{name}: 안전을 위해서는... {hint} 이 방법을 권장합니다.",
            'encouraging': f"{name}: 힌트를 드릴게요! {hint} 이제 해결할 수 있을 거예요!",
            'neutral': f"{name}: {hint}"
        }
        
        return style_wrappers.get(style, f"{name}: {hint}")
    
    def _generate_ai_hint(self, question_data: Dict, hint_level: int, npc: Dict) -> str:
        """
        AI를 활용한 동적 힌트 생성
        """
        if not q_cli.cli_available:
            return "죄송해요, 지금은 추가 힌트를 제공할 수 없어요."
        
        # NPC 성격을 반영한 힌트 생성 프롬프트
        personality_context = f"당신은 {npc['title']} {npc['name']}입니다. {npc['personality']['type']} 성격을 가지고 있습니다."
        
        prompt = f"""
        {personality_context}
        
        다음 AWS 문제에 대해 {hint_level}단계 힌트를 제공해주세요:
        
        문제: {question_data.get('question', '')}
        시나리오: {question_data.get('scenario', {}).get('description', '')}
        
        힌트는 {npc['name']}의 성격과 전문성을 반영하여 작성해주세요.
        직접적인 답은 주지 말고, 해결 방향을 제시하는 형태로 작성해주세요.
        """
        
        ai_hint = q_cli.ask_question(prompt)
        return ai_hint or "좀 더 생각해보시면 답을 찾을 수 있을 거예요!"
    
    def _enhance_response_with_ai(self, npc: Dict, response: str, user_message: str, context: Dict) -> Optional[str]:
        """
        AI를 활용한 응답 개선
        """
        if not q_cli.cli_available or random.random() > 0.3:  # 30% 확률로만 AI 개선 적용
            return None
        
        prompt = f"""
        당신은 {npc['title']} {npc['name']}입니다.
        성격: {npc['personality']['type']}
        전문분야: {', '.join(npc['expertise']['primary'])}
        
        사용자가 "{user_message}"라고 말했을 때,
        기본 응답 "{response}"를 {npc['name']}의 성격과 전문성에 맞게 더 자연스럽고 도움이 되도록 개선해주세요.
        
        응답은 한국어로 작성하고, 캐릭터의 일관성을 유지해주세요.
        """
        
        enhanced = q_cli.ask_question(prompt)
        return enhanced if enhanced and len(enhanced) < 200 else None
    
    def _get_conversation_options(self, npc: Dict, response_type: str) -> List[Dict]:
        """
        대화 옵션 생성
        """
        base_options = [
            {"id": "continue", "text": "계속하기", "type": "continue"},
            {"id": "hint", "text": "힌트 요청", "type": "hint"},
            {"id": "explain", "text": "더 자세히 설명해주세요", "type": "explain"}
        ]
        
        # NPC별 특별 옵션 추가
        if npc['personality']['type'] == 'energetic':
            base_options.append({"id": "urgent", "text": "빠른 해결책이 필요해요", "type": "urgent"})
        elif npc['personality']['type'] == 'analytical':
            base_options.append({"id": "data", "text": "데이터를 보여주세요", "type": "data"})
        
        return base_options
    
    def _get_personality_indicators(self, npc: Dict, response_type: str) -> Dict:
        """
        성격 지표 반환 (UI에서 활용)
        """
        return {
            'personality_type': npc['personality']['type'],
            'traits': npc['personality']['traits'],
            'urgency_level': npc['personality']['urgency_level'],
            'communication_style': npc['personality']['communication_style']
        }
    
    def _add_to_history(self, user_id: str, session_id: str, speaker: str, message: str, context: Dict = None):
        """
        대화 히스토리에 추가
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {}
        
        if session_id not in self.conversation_history[user_id]:
            self.conversation_history[user_id][session_id] = []
        
        self.conversation_history[user_id][session_id].append({
            'speaker': speaker,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        })
    
    def _get_scenario_info(self, scenario_id: str) -> Optional[Dict]:
        """
        시나리오 정보 반환
        """
        if scenario_id in self.scenarios.get('scenarios', {}):
            scenario = self.scenarios['scenarios'][scenario_id]
            return {
                'id': scenario_id,
                'title': scenario['title'],
                'description': scenario['description'],
                'difficulty': scenario['difficulty'],
                'duration': scenario['duration']
            }
        return None
    
    def _create_error_response(self, error_message: str) -> Dict:
        """
        에러 응답 생성
        """
        return {
            'error': True,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_default_npc_data(self) -> Dict:
        """
        기본 NPC 데이터 반환 (파일 로드 실패 시)
        """
        return {
            "npcs": {
                "alex_ceo": {
                    "name": "Alex",
                    "title": "CEO",
                    "personality": {"type": "energetic"},
                    "expertise": {"primary": ["EC2"]},
                    "dialogue": {
                        "greeting": "안녕하세요! 도움이 필요해요!",
                        "correct_response": ["훌륭해요!"],
                        "incorrect_response": ["다시 생각해보세요."],
                        "hint_request": ["힌트를 드릴게요."]
                    }
                }
            }
        }
    
    def get_conversation_history(self, user_id: str, session_id: str = None) -> Dict:
        """
        대화 히스토리 조회
        """
        if user_id not in self.conversation_history:
            return {"history": []}
        
        if session_id:
            return {
                "history": self.conversation_history[user_id].get(session_id, [])
            }
        
        return {
            "sessions": list(self.conversation_history[user_id].keys()),
            "total_conversations": sum(len(conv) for conv in self.conversation_history[user_id].values())
        }
    
    def end_conversation(self, session_id: str) -> Dict:
        """
        대화 종료
        """
        if session_id in self.current_sessions:
            session = self.current_sessions[session_id]
            session['end_time'] = datetime.now().isoformat()
            
            # 세션 통계 계산
            duration = datetime.now() - datetime.fromisoformat(session['start_time'])
            
            result = {
                'session_id': session_id,
                'duration_minutes': duration.total_seconds() / 60,
                'conversation_count': session['conversation_count'],
                'npc_id': session['npc_id'],
                'scenario_id': session.get('scenario_id'),
                'ended_at': session['end_time']
            }
            
            # 활성 세션에서 제거
            del self.current_sessions[session_id]
            
            return result
        
        return self._create_error_response("세션을 찾을 수 없습니다.")

# 전역 인스턴스
dialogue_engine = NPCDialogueEngine()

# 편의 함수들
def start_npc_conversation(user_id: str, npc_id: str, scenario_id: str = None) -> Dict:
    """
    NPC 대화 시작 편의 함수
    """
    return dialogue_engine.start_conversation(user_id, npc_id, scenario_id)

def continue_npc_conversation(session_id: str, user_message: str, context: Dict = None) -> Dict:
    """
    NPC 대화 계속 편의 함수
    """
    return dialogue_engine.continue_conversation(session_id, user_message, context)

def get_npc_hint(session_id: str, question_data: Dict, hint_level: int) -> Dict:
    """
    NPC 힌트 요청 편의 함수
    """
    return dialogue_engine.get_hint_response(session_id, question_data, hint_level)
