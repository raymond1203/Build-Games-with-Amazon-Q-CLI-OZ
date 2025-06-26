"""
AWS Problem Solver Game - Amazon Q CLI Integration
Amazon Q CLI와의 연동을 담당하는 유틸리티 모듈
"""

import subprocess
import json
import os
import asyncio
from typing import Dict, List, Optional, Union
from datetime import datetime

class AmazonQCLIIntegration:
    """
    Amazon Q CLI 연동 클래스
    """
    
    def __init__(self, timeout: int = 30):
        """
        초기화
        
        Args:
            timeout: CLI 명령어 실행 타임아웃 (초)
        """
        self.timeout = timeout
        self.cli_available = self._check_cli_availability()
    
    def _check_cli_availability(self) -> bool:
        """
        Amazon Q CLI 사용 가능 여부 확인
        """
        try:
            result = subprocess.run(
                ['q', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def ask_question(self, question: str, context: str = '') -> Optional[str]:
        """
        Amazon Q CLI에 질문하기
        
        Args:
            question: 질문 내용
            context: 추가 컨텍스트 정보
            
        Returns:
            Q CLI 응답 또는 None (실패 시)
        """
        if not self.cli_available:
            return None
        
        try:
            # 컨텍스트가 있으면 질문에 포함
            full_question = self._format_question(question, context)
            
            # Q CLI 명령어 실행 (stdin으로 질문 전달)
            result = subprocess.run(
                ['q', 'chat'],
                input=full_question,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=dict(os.environ)
            )
            
            if result.returncode == 0:
                return self._clean_response(result.stdout)
            else:
                print(f"Q CLI error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Q CLI timeout")
            return None
        except Exception as e:
            print(f"Error calling Q CLI: {str(e)}")
            return None
    
    def get_aws_explanation(self, service: str, concept: str, level: str = 'basic') -> Optional[str]:
        """
        AWS 서비스/개념 설명 요청
        
        Args:
            service: AWS 서비스 이름 (예: EC2, S3)
            concept: 설명할 개념 (예: Auto Scaling, Load Balancer)
            level: 설명 수준 (basic, intermediate, advanced)
            
        Returns:
            설명 내용 또는 None
        """
        level_prompts = {
            'basic': '초보자도 이해할 수 있도록 간단하게',
            'intermediate': '실무에서 활용할 수 있는 수준으로',
            'advanced': '깊이 있는 기술적 세부사항을 포함하여'
        }
        
        question = f"""
        AWS {service}의 {concept}에 대해 {level_prompts.get(level, '간단하게')} 설명해주세요.
        
        다음 내용을 포함해주세요:
        1. 기본 개념과 목적
        2. 주요 기능과 특징
        3. 실무 사용 사례
        4. 관련 서비스와의 연관성
        
        설명은 한국어로 작성하고, 구체적인 예시를 포함해주세요.
        """
        
        return self.ask_question(question)
    
    def generate_hint(self, question_data: Dict, hint_level: int) -> Optional[str]:
        """
        문제에 대한 힌트 생성
        
        Args:
            question_data: 문제 데이터
            hint_level: 힌트 레벨 (1-3)
            
        Returns:
            생성된 힌트 또는 None
        """
        category = question_data.get('category', '')
        difficulty = question_data.get('difficulty', '')
        scenario = question_data.get('scenario', {})
        question_text = question_data.get('question', '')
        
        hint_prompts = {
            1: f"""
            다음 AWS {category} 관련 문제에 대해 해결 방향을 제시하는 힌트를 주세요:
            
            시나리오: {scenario.get('description', '')}
            문제: {question_text}
            
            힌트는 직접적인 답을 주지 말고, 고려해야 할 AWS 서비스나 개념을 제안하는 형태로 작성해주세요.
            """,
            2: f"""
            AWS {category} 관련 {difficulty} 난이도 문제에 대해 좀 더 구체적인 힌트를 주세요:
            
            컨텍스트: {scenario.get('context', '')}
            
            어떤 AWS 서비스들을 조합해서 사용해야 하는지 방향을 제시해주세요.
            """,
            3: f"""
            다음 AWS 문제의 해결책에 대해 거의 정답에 가까운 힌트를 주세요:
            
            시나리오: {scenario.get('description', '')}
            문제: {question_text}
            
            구체적인 AWS 서비스 이름과 설정 방법을 포함해서 설명해주세요.
            """
        }
        
        prompt = hint_prompts.get(hint_level, hint_prompts[1])
        return self.ask_question(prompt)
    
    def get_best_practices(self, service: str, scenario: str) -> Optional[str]:
        """
        AWS 모범 사례 조언
        
        Args:
            service: AWS 서비스
            scenario: 시나리오 설명
            
        Returns:
            모범 사례 조언 또는 None
        """
        question = f"""
        다음 시나리오에서 AWS {service}를 사용할 때의 모범 사례를 알려주세요:
        
        시나리오: {scenario}
        
        다음 관점에서 조언해주세요:
        1. 보안 측면
        2. 성능 최적화
        3. 비용 효율성
        4. 고가용성
        
        실무에서 바로 적용할 수 있는 구체적인 팁을 포함해주세요.
        """
        
        return self.ask_question(question)
    
    def validate_solution(self, question_data: Dict, user_answer: str) -> Optional[str]:
        """
        사용자 답안에 대한 검증 및 피드백
        
        Args:
            question_data: 문제 데이터
            user_answer: 사용자가 선택한 답안
            
        Returns:
            검증 결과 및 피드백 또는 None
        """
        scenario = question_data.get('scenario', {})
        question_text = question_data.get('question', '')
        options = question_data.get('options', [])
        
        # 선택한 답안의 텍스트 찾기
        selected_option_text = ""
        for option in options:
            if option.get('id') == user_answer:
                selected_option_text = option.get('text', '')
                break
        
        question = f"""
        다음 AWS 문제에 대한 답안을 검증하고 피드백을 주세요:
        
        시나리오: {scenario.get('description', '')}
        문제: {question_text}
        선택한 답안: {selected_option_text}
        
        다음 내용을 포함해서 답변해주세요:
        1. 선택한 답안이 적절한지 여부
        2. 해당 솔루션의 장단점
        3. 대안적인 접근 방법이 있다면 제시
        4. 실무에서 고려해야 할 추가 사항
        
        건설적인 피드백으로 학습에 도움이 되도록 작성해주세요.
        """
        
        return self.ask_question(question)
    
    def _format_question(self, question: str, context: str = '') -> str:
        """
        질문 포맷팅
        """
        if context:
            return f"컨텍스트: {context}\n\n질문: {question}"
        return question
    
    def _clean_response(self, response: str) -> str:
        """
        응답 정리 (불필요한 문자 제거 등)
        """
        # 기본적인 정리 작업
        cleaned = response.strip()
        
        # CLI 출력에서 불필요한 부분 제거
        lines = cleaned.split('\n')
        content_lines = []
        
        for line in lines:
            # 시스템 메시지나 프롬프트 제거 (줄의 시작 부분만 체크)
            line_stripped = line.strip()
            if not (line_stripped.startswith('q>') or line_stripped.startswith('Amazon Q>')):
                content_lines.append(line)
        
        return '\n'.join(content_lines).strip()

# 전역 인스턴스
q_cli = AmazonQCLIIntegration()

# 편의 함수들
def ask_q(question: str, context: str = '') -> Optional[str]:
    """
    간단한 Q CLI 질문 함수
    """
    return q_cli.ask_question(question, context)

def get_aws_help(service: str, concept: str, level: str = 'basic') -> Optional[str]:
    """
    AWS 도움말 요청 함수
    """
    return q_cli.get_aws_explanation(service, concept, level)

def generate_question_hint(question_data: Dict, hint_level: int = 1) -> Optional[str]:
    """
    문제 힌트 생성 함수
    """
    return q_cli.generate_hint(question_data, hint_level)

def get_solution_feedback(question_data: Dict, user_answer: str) -> Optional[str]:
    """
    솔루션 피드백 함수
    """
    return q_cli.validate_solution(question_data, user_answer)

def is_q_cli_available() -> bool:
    """
    Q CLI 사용 가능 여부 확인
    """
    return q_cli.cli_available
