"""
Amazon Q CLI Integration Tests
Q CLI 연동 기능 테스트
"""

import unittest
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.q_cli_integration import (
    AmazonQCLIIntegration, 
    ask_q, 
    get_aws_help, 
    generate_question_hint,
    is_q_cli_available
)

class TestAmazonQCLIIntegration(unittest.TestCase):
    """
    Amazon Q CLI 연동 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        self.q_cli = AmazonQCLIIntegration(timeout=10)
        
        # 테스트용 문제 데이터
        self.sample_question = {
            'questionId': 'test_q_001',
            'category': 'EC2',
            'difficulty': 'medium',
            'scenario': {
                'title': '트래픽 급증 문제',
                'description': '웹사이트 트래픽이 갑자기 10배 증가했습니다.',
                'context': '현재 단일 EC2 인스턴스로 운영 중입니다.'
            },
            'question': '이 상황을 해결하기 위한 가장 적절한 AWS 솔루션은?',
            'options': [
                {'id': 'A', 'text': '더 큰 인스턴스로 업그레이드'},
                {'id': 'B', 'text': 'Auto Scaling Group 구성'},
                {'id': 'C', 'text': 'CloudFront만 추가'},
                {'id': 'D', 'text': 'RDS 추가'}
            ]
        }
    
    def test_cli_availability_check(self):
        """
        CLI 사용 가능 여부 확인 테스트
        """
        # CLI가 설치되어 있지 않을 수 있으므로 결과에 관계없이 테스트 통과
        availability = self.q_cli._check_cli_availability()
        self.assertIsInstance(availability, bool)
        print(f"Q CLI Available: {availability}")
    
    @patch('subprocess.run')
    def test_ask_question_success(self, mock_subprocess):
        """
        질문 성공 케이스 테스트
        """
        # Mock 설정
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "EC2 Auto Scaling을 사용하면 트래픽에 따라 자동으로 인스턴스를 조절할 수 있습니다."
        mock_subprocess.return_value = mock_result
        
        # 테스트 실행
        response = self.q_cli.ask_question("EC2 Auto Scaling이 뭔가요?")
        
        # 검증
        self.assertIsNotNone(response)
        self.assertIn("Auto Scaling", response)
        mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_ask_question_timeout(self, mock_subprocess):
        """
        질문 타임아웃 케이스 테스트
        """
        # Mock 설정 - 타임아웃 발생
        mock_subprocess.side_effect = subprocess.TimeoutExpired(['q', 'chat'], 30)
        
        # 테스트 실행
        response = self.q_cli.ask_question("테스트 질문")
        
        # 검증
        self.assertIsNone(response)
    
    @patch('subprocess.run')
    def test_get_aws_explanation(self, mock_subprocess):
        """
        AWS 설명 요청 테스트
        """
        # Mock 설정
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        EC2 Auto Scaling은 애플리케이션의 로드를 처리할 수 있는 정확한 수의 EC2 인스턴스를 유지하도록 도와주는 서비스입니다.
        
        주요 기능:
        1. 자동 확장 및 축소
        2. 상태 확인 및 교체
        3. 로드 밸런싱과 통합
        """
        mock_subprocess.return_value = mock_result
        
        # 테스트 실행
        response = self.q_cli.get_aws_explanation("EC2", "Auto Scaling", "basic")
        
        # 검증
        self.assertIsNotNone(response)
        self.assertIn("Auto Scaling", response)
        self.assertIn("EC2", response)
    
    @patch('subprocess.run')
    def test_generate_hint(self, mock_subprocess):
        """
        힌트 생성 테스트
        """
        # Mock 설정
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "트래픽 급증에 대응하려면 수평적 확장을 고려해보세요. AWS에는 자동으로 서버 개수를 조절하는 서비스가 있습니다."
        mock_subprocess.return_value = mock_result
        
        # 테스트 실행
        hint = self.q_cli.generate_hint(self.sample_question, 1)
        
        # 검증
        self.assertIsNotNone(hint)
        self.assertIn("확장", hint)
    
    def test_format_question(self):
        """
        질문 포맷팅 테스트
        """
        question = "EC2란 무엇인가요?"
        context = "클라우드 컴퓨팅 서비스에 대해 알고 싶습니다."
        
        formatted = self.q_cli._format_question(question, context)
        
        self.assertIn("컨텍스트:", formatted)
        self.assertIn("질문:", formatted)
        self.assertIn(question, formatted)
        self.assertIn(context, formatted)
    
    def test_clean_response(self):
        """
        응답 정리 테스트
        """
        raw_response = """
        q> 질문을 입력하세요
        Amazon Q> EC2는 Elastic Compute Cloud의 줄임말입니다.
        
        주요 특징:
        - 가상 서버 제공
        - 다양한 인스턴스 타입
        """
        
        cleaned = self.q_cli._clean_response(raw_response)
        
        # 시스템 프롬프트가 제거되었는지 확인
        self.assertNotIn("q>", cleaned)
        self.assertNotIn("Amazon Q>", cleaned)
        self.assertIn("EC2는", cleaned)
        self.assertIn("주요 특징", cleaned)

class TestConvenienceFunctions(unittest.TestCase):
    """
    편의 함수들 테스트
    """
    
    @patch('utils.q_cli_integration.q_cli')
    def test_ask_q_function(self, mock_q_cli):
        """
        ask_q 편의 함수 테스트
        """
        mock_q_cli.ask_question.return_value = "테스트 응답"
        
        result = ask_q("테스트 질문", "테스트 컨텍스트")
        
        self.assertEqual(result, "테스트 응답")
        mock_q_cli.ask_question.assert_called_once_with("테스트 질문", "테스트 컨텍스트")
    
    @patch('utils.q_cli_integration.q_cli')
    def test_get_aws_help_function(self, mock_q_cli):
        """
        get_aws_help 편의 함수 테스트
        """
        mock_q_cli.get_aws_explanation.return_value = "AWS 도움말"
        
        result = get_aws_help("EC2", "Auto Scaling", "intermediate")
        
        self.assertEqual(result, "AWS 도움말")
        mock_q_cli.get_aws_explanation.assert_called_once_with("EC2", "Auto Scaling", "intermediate")
    
    @patch('utils.q_cli_integration.q_cli')
    def test_generate_question_hint_function(self, mock_q_cli):
        """
        generate_question_hint 편의 함수 테스트
        """
        mock_q_cli.generate_hint.return_value = "생성된 힌트"
        question_data = {'category': 'EC2'}
        
        result = generate_question_hint(question_data, 2)
        
        self.assertEqual(result, "생성된 힌트")
        mock_q_cli.generate_hint.assert_called_once_with(question_data, 2)
    
    @patch('utils.q_cli_integration.q_cli')
    def test_is_q_cli_available_function(self, mock_q_cli):
        """
        is_q_cli_available 편의 함수 테스트
        """
        mock_q_cli.cli_available = True
        
        result = is_q_cli_available()
        
        self.assertTrue(result)

class TestIntegrationScenarios(unittest.TestCase):
    """
    통합 시나리오 테스트
    """
    
    def setUp(self):
        self.q_cli = AmazonQCLIIntegration()
    
    @patch('subprocess.run')
    def test_full_hint_generation_workflow(self, mock_subprocess):
        """
        전체 힌트 생성 워크플로우 테스트
        """
        # Mock 설정 - 단계별 힌트
        mock_responses = [
            "1단계 힌트: 트래픽 분산을 고려해보세요.",
            "2단계 힌트: Auto Scaling Group을 사용해보세요.",
            "3단계 힌트: Application Load Balancer와 함께 사용하세요."
        ]
        
        mock_results = []
        for response in mock_responses:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = response
            mock_results.append(mock_result)
        
        mock_subprocess.side_effect = mock_results
        
        question_data = {
            'category': 'EC2',
            'difficulty': 'medium',
            'scenario': {'description': '트래픽 급증 문제'},
            'question': '해결 방법은?'
        }
        
        # 단계별 힌트 테스트
        for level in range(1, 4):
            hint = self.q_cli.generate_hint(question_data, level)
            self.assertIsNotNone(hint)
            self.assertIn(f"{level}단계", hint)
    
    def test_error_handling(self):
        """
        에러 처리 테스트
        """
        # CLI가 없는 경우
        with patch.object(self.q_cli, 'cli_available', False):
            result = self.q_cli.ask_question("테스트")
            self.assertIsNone(result)
        
        # 빈 질문인 경우
        result = self.q_cli.ask_question("")
        # 빈 질문도 처리되어야 함 (CLI가 있다면)

if __name__ == '__main__':
    # 테스트 실행
    print("Amazon Q CLI Integration Tests")
    print("=" * 50)
    
    # 실제 CLI 사용 가능 여부 확인
    q_cli_test = AmazonQCLIIntegration()
    print(f"Q CLI Available: {q_cli_test.cli_available}")
    
    if q_cli_test.cli_available:
        print("✅ Amazon Q CLI가 사용 가능합니다.")
        
        # 간단한 실제 테스트
        print("\n실제 Q CLI 테스트:")
        response = q_cli_test.ask_question("AWS EC2란 무엇인가요? 간단히 설명해주세요.")
        if response:
            print(f"응답: {response[:100]}...")
        else:
            print("응답을 받지 못했습니다.")
    else:
        print("⚠️  Amazon Q CLI를 사용할 수 없습니다.")
        print("   - Q CLI가 설치되어 있는지 확인하세요.")
        print("   - 'q --version' 명령어로 설치 상태를 확인할 수 있습니다.")
    
    print("\n" + "=" * 50)
    
    # 단위 테스트 실행
    unittest.main(verbosity=2)
