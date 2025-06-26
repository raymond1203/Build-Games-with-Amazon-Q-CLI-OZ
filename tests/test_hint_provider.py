"""
AWS Problem Solver Game - Hint Provider 단위 테스트
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import subprocess

# 테스트를 위해 Lambda 함수 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_functions'))

from hint_provider import AmazonQHintProvider, lambda_handler


class TestAmazonQHintProvider(unittest.TestCase):
    """Amazon Q Hint Provider 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.hint_provider = AmazonQHintProvider()
        
        # 테스트용 문제 데이터
        self.test_question_data = {
            'questionId': 'test_q001',
            'category': 'EC2',
            'difficulty': 'medium',
            'scenario': {
                'title': '웹 애플리케이션 확장성 문제',
                'description': '트래픽이 급증하여 단일 EC2 인스턴스의 CPU 사용률이 90%를 넘고 있습니다.',
                'context': '현재 단일 EC2 인스턴스에서 실행 중이며, 피크 시간대에 응답 시간이 느려지고 있습니다.'
            },
            'question': '이 상황에서 가장 적절한 AWS 솔루션은 무엇입니까?'
        }
    
    def test_init(self):
        """초기화 테스트"""
        self.assertIsInstance(self.hint_provider, AmazonQHintProvider)
        self.assertIn('alex_ceo', self.hint_provider.npc_hint_styles)
        self.assertIn('sarah_analyst', self.hint_provider.npc_hint_styles)
        self.assertIn('mike_security', self.hint_provider.npc_hint_styles)
        self.assertIn('jenny_developer', self.hint_provider.npc_hint_styles)
    
    @patch('hint_provider.subprocess.run')
    def test_check_q_cli_availability_success(self, mock_subprocess):
        """Amazon Q CLI 사용 가능 테스트"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        provider = AmazonQHintProvider()
        self.assertTrue(provider.q_cli_available)
    
    @patch('hint_provider.subprocess.run')
    def test_check_q_cli_availability_failure(self, mock_subprocess):
        """Amazon Q CLI 사용 불가 테스트"""
        mock_subprocess.side_effect = FileNotFoundError()
        
        provider = AmazonQHintProvider()
        self.assertFalse(provider.q_cli_available)
    
    def test_build_question_context(self):
        """문제 컨텍스트 구축 테스트"""
        context = self.hint_provider._build_question_context(self.test_question_data)
        
        self.assertEqual(context['category'], 'EC2')
        self.assertEqual(context['difficulty'], 'medium')
        self.assertIn('트래픽이 급증', context['scenario'])
        self.assertIn('적절한 AWS 솔루션', context['question'])
    
    def test_generate_fallback_hint_ec2(self):
        """EC2 대체 힌트 생성 테스트"""
        hint_result = self.hint_provider._generate_fallback_hint(
            self.test_question_data, 'alex_ceo', 1
        )
        
        self.assertIn('hint', hint_result)
        self.assertIn('source', hint_result)
        self.assertEqual(hint_result['source'], 'fallback')
        self.assertEqual(hint_result['npc_id'], 'alex_ceo')
        self.assertEqual(hint_result['hint_level'], 1)
        self.assertTrue(hint_result['success'])
    
    def test_generate_fallback_hint_all_levels(self):
        """모든 힌트 레벨 테스트"""
        for level in [1, 2, 3]:
            hint_result = self.hint_provider._generate_fallback_hint(
                self.test_question_data, 'sarah_analyst', level
            )
            
            self.assertEqual(hint_result['hint_level'], level)
            self.assertIsInstance(hint_result['hint'], str)
            self.assertTrue(len(hint_result['hint']) > 0)
    
    def test_generate_fallback_hint_all_npcs(self):
        """모든 NPC 힌트 테스트"""
        npcs = ['alex_ceo', 'sarah_analyst', 'mike_security', 'jenny_developer']
        
        for npc_id in npcs:
            hint_result = self.hint_provider._generate_fallback_hint(
                self.test_question_data, npc_id, 1
            )
            
            self.assertEqual(hint_result['npc_id'], npc_id)
            self.assertIsInstance(hint_result['hint'], str)
    
    def test_apply_npc_style(self):
        """NPC 스타일 적용 테스트"""
        base_hint = "Auto Scaling Group을 고려해보세요."
        npc_style = self.hint_provider.npc_hint_styles['alex_ceo']
        
        styled_hint = self.hint_provider._apply_npc_style(
            base_hint, 'alex_ceo', npc_style
        )
        
        self.assertNotEqual(styled_hint, base_hint)
        self.assertIn(base_hint, styled_hint)
    
    def test_get_fallback_explanation_ec2(self):
        """EC2 대체 설명 테스트"""
        explanation_result = self.hint_provider._get_fallback_explanation('EC2', '')
        
        self.assertIn('explanation', explanation_result)
        self.assertIn('service', explanation_result)
        self.assertEqual(explanation_result['service'], 'EC2')
        self.assertEqual(explanation_result['source'], 'fallback')
        self.assertTrue(explanation_result['success'])
        self.assertIn('Amazon EC2', explanation_result['explanation'])
    
    def test_get_fallback_explanation_unknown_service(self):
        """알려지지 않은 서비스 설명 테스트"""
        explanation_result = self.hint_provider._get_fallback_explanation('UnknownService', '')
        
        self.assertIn('UnknownService', explanation_result['explanation'])
        self.assertIn('상세 정보를 현재 제공할 수 없습니다', explanation_result['explanation'])
    
    @patch('hint_provider.subprocess.run')
    def test_generate_q_cli_hint_success(self, mock_subprocess):
        """Amazon Q CLI 힌트 생성 성공 테스트"""
        # Q CLI 사용 가능하도록 설정
        self.hint_provider.q_cli_available = True
        
        # Mock Q CLI 응답
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'response': 'Auto Scaling Group과 Load Balancer를 고려해보세요.'
        })
        mock_subprocess.return_value = mock_result
        
        hint_result = self.hint_provider._generate_q_cli_hint(
            self.test_question_data, 'alex_ceo', 1
        )
        
        self.assertEqual(hint_result['source'], 'amazon_q')
        self.assertTrue(hint_result['success'])
        self.assertIn('Auto Scaling', hint_result['hint'])
    
    @patch('hint_provider.subprocess.run')
    def test_generate_q_cli_hint_failure(self, mock_subprocess):
        """Amazon Q CLI 힌트 생성 실패 테스트"""
        # Q CLI 사용 가능하도록 설정
        self.hint_provider.q_cli_available = True
        
        # Mock Q CLI 실패
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = 'Q CLI Error'
        mock_subprocess.return_value = mock_result
        
        hint_result = self.hint_provider._generate_q_cli_hint(
            self.test_question_data, 'alex_ceo', 1
        )
        
        # 실패 시 대체 힌트로 전환되어야 함
        self.assertEqual(hint_result['source'], 'fallback')
    
    def test_generate_hint_with_q_cli_unavailable(self):
        """Q CLI 사용 불가 시 힌트 생성 테스트"""
        self.hint_provider.q_cli_available = False
        
        hint_result = self.hint_provider.generate_hint(
            self.test_question_data, 'alex_ceo', 1
        )
        
        self.assertEqual(hint_result['source'], 'fallback')
        self.assertTrue(hint_result['success'])
    
    def test_get_aws_explanation_with_q_cli_unavailable(self):
        """Q CLI 사용 불가 시 AWS 설명 테스트"""
        self.hint_provider.q_cli_available = False
        
        explanation_result = self.hint_provider.get_aws_explanation('S3', '')
        
        self.assertEqual(explanation_result['source'], 'fallback')
        self.assertTrue(explanation_result['success'])
        self.assertIn('S3', explanation_result['explanation'])


class TestLambdaHandler(unittest.TestCase):
    """Lambda 핸들러 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_context = Mock()
    
    def test_lambda_handler_get_hint(self):
        """힌트 요청 Lambda 핸들러 테스트"""
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'action': 'get_hint',
                'questionData': {
                    'category': 'EC2',
                    'difficulty': 'medium',
                    'scenario': {
                        'description': '트래픽 급증 문제'
                    },
                    'question': '적절한 솔루션은?'
                },
                'npcId': 'alex_ceo',
                'hintLevel': 1
            })
        }
        
        response = lambda_handler(event, self.test_context)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Content-Type', response['headers'])
        
        body = json.loads(response['body'])
        self.assertIn('hint', body)
        self.assertIn('source', body)
    
    def test_lambda_handler_get_explanation(self):
        """설명 요청 Lambda 핸들러 테스트"""
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'action': 'get_explanation',
                'serviceName': 'EC2',
                'context': '웹 애플리케이션 호스팅'
            })
        }
        
        response = lambda_handler(event, self.test_context)
        
        self.assertEqual(response['statusCode'], 200)
        
        body = json.loads(response['body'])
        self.assertIn('explanation', body)
        self.assertIn('service', body)
    
    def test_lambda_handler_options_request(self):
        """OPTIONS 요청 (CORS preflight) 테스트"""
        event = {
            'httpMethod': 'OPTIONS'
        }
        
        response = lambda_handler(event, self.test_context)
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertIn('Access-Control-Allow-Methods', response['headers'])
    
    def test_lambda_handler_invalid_action(self):
        """잘못된 액션 요청 테스트"""
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'action': 'invalid_action'
            })
        }
        
        response = lambda_handler(event, self.test_context)
        
        self.assertEqual(response['statusCode'], 400)
        
        body = json.loads(response['body'])
        self.assertIn('error', body)
    
    def test_lambda_handler_malformed_json(self):
        """잘못된 JSON 요청 테스트"""
        event = {
            'httpMethod': 'POST',
            'body': 'invalid json'
        }
        
        response = lambda_handler(event, self.test_context)
        
        self.assertEqual(response['statusCode'], 500)
    
    def test_lambda_handler_no_body(self):
        """본문 없는 요청 테스트"""
        event = {
            'httpMethod': 'POST'
        }
        
        response = lambda_handler(event, self.test_context)
        
        self.assertEqual(response['statusCode'], 400)


class TestIntegration(unittest.TestCase):
    """통합 테스트 클래스"""
    
    def test_end_to_end_hint_generation(self):
        """엔드투엔드 힌트 생성 테스트"""
        provider = AmazonQHintProvider()
        
        question_data = {
            'category': 'S3',
            'difficulty': 'easy',
            'scenario': {
                'description': '데이터 백업이 필요합니다.'
            },
            'question': '적절한 스토리지 클래스는?'
        }
        
        # 모든 NPC와 모든 레벨 조합 테스트
        npcs = ['alex_ceo', 'sarah_analyst', 'mike_security', 'jenny_developer']
        levels = [1, 2, 3]
        
        for npc_id in npcs:
            for level in levels:
                hint_result = provider.generate_hint(question_data, npc_id, level)
                
                self.assertTrue(hint_result['success'])
                self.assertIn('hint', hint_result)
                self.assertEqual(hint_result['npc_id'], npc_id)
                self.assertEqual(hint_result['hint_level'], level)
    
    def test_service_explanation_coverage(self):
        """서비스 설명 커버리지 테스트"""
        provider = AmazonQHintProvider()
        
        # 주요 AWS 서비스들 테스트
        services = ['EC2', 'S3', 'Lambda', 'RDS', 'VPC', 'IAM', 'CloudWatch']
        
        for service in services:
            explanation_result = provider.get_aws_explanation(service, '')
            
            self.assertTrue(explanation_result['success'])
            self.assertIn('explanation', explanation_result)
            self.assertIn(service, explanation_result['explanation'])


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
