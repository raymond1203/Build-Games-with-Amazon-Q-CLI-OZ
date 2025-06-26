#!/usr/bin/env python3
"""
AWS Problem Solver Game - 통합 테스트 스위트
전체 시스템의 엔드투엔드 테스트
"""

import unittest
import requests
import json
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

class IntegrationTestSuite(unittest.TestCase):
    """통합 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:8000')
        cls.api_url = os.getenv('TEST_API_URL', 'https://your-api-gateway-url/dev')
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 헤드리스 모드
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 10)
        except WebDriverException as e:
            print(f"Chrome WebDriver 초기화 실패: {e}")
            print("Chrome WebDriver가 설치되어 있는지 확인하세요.")
            cls.driver = None
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        if cls.driver:
            cls.driver.quit()
    
    def setUp(self):
        """각 테스트 전 설정"""
        if not self.driver:
            self.skipTest("WebDriver를 사용할 수 없습니다.")
    
    def test_01_homepage_load(self):
        """홈페이지 로딩 테스트"""
        print("\n🧪 홈페이지 로딩 테스트...")
        
        try:
            self.driver.get(self.base_url)
            
            # 페이지 제목 확인
            self.assertIn("AWS Problem Solver Game", self.driver.title)
            
            # 로딩 화면이 사라질 때까지 대기
            self.wait.until(
                EC.invisibility_of_element_located((By.ID, "loading-screen"))
            )
            
            # 웰컴 화면 표시 확인
            welcome_screen = self.wait.until(
                EC.visibility_of_element_located((By.ID, "welcome-screen"))
            )
            self.assertTrue(welcome_screen.is_displayed())
            
            print("✅ 홈페이지 로딩 성공")
            
        except TimeoutException:
            self.fail("홈페이지 로딩 시간 초과")
        except Exception as e:
            self.fail(f"홈페이지 로딩 실패: {e}")
    
    def test_02_game_start_flow(self):
        """게임 시작 플로우 테스트"""
        print("\n🧪 게임 시작 플로우 테스트...")
        
        try:
            self.driver.get(self.base_url)
            
            # 로딩 완료 대기
            self.wait.until(
                EC.invisibility_of_element_located((By.ID, "loading-screen"))
            )
            
            # 사용자 이름 입력
            username_input = self.wait.until(
                EC.element_to_be_clickable((By.ID, "username-input"))
            )
            username_input.clear()
            username_input.send_keys("TestUser")
            
            # 게임 모드 선택
            mode_card = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-mode='practice']"))
            )
            mode_card.click()
            
            # 게임 시작 버튼 클릭
            start_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "start-game-btn"))
            )
            start_button.click()
            
            # NPC 선택 화면으로 이동 확인
            npc_selection = self.wait.until(
                EC.visibility_of_element_located((By.ID, "npc-selection-screen"))
            )
            self.assertTrue(npc_selection.is_displayed())
            
            print("✅ 게임 시작 플로우 성공")
            
        except TimeoutException:
            self.fail("게임 시작 플로우 시간 초과")
        except Exception as e:
            self.fail(f"게임 시작 플로우 실패: {e}")
    
    def test_03_npc_selection_and_dialogue(self):
        """NPC 선택 및 대화 테스트"""
        print("\n🧪 NPC 선택 및 대화 테스트...")
        
        try:
            # 게임 시작까지 진행
            self._start_game_to_npc_selection()
            
            # NPC 선택 (Alex CEO)
            npc_card = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-npc='alex_ceo']"))
            )
            npc_card.click()
            
            # 게임 화면으로 이동 확인
            game_screen = self.wait.until(
                EC.visibility_of_element_located((By.ID, "game-screen"))
            )
            self.assertTrue(game_screen.is_displayed())
            
            # NPC 대화 영역 표시 확인 (잠시 후)
            time.sleep(2)
            
            # 대화 건너뛰기 (대화가 있다면)
            try:
                skip_btn = self.driver.find_element(By.ID, "skip-dialogue-btn")
                if skip_btn.is_displayed():
                    skip_btn.click()
            except:
                pass  # 대화가 없거나 이미 완료됨
            
            # 문제 영역 표시 확인
            question_area = self.wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "question-area"))
            )
            self.assertTrue(question_area.is_displayed())
            
            print("✅ NPC 선택 및 대화 성공")
            
        except TimeoutException:
            self.fail("NPC 선택 및 대화 시간 초과")
        except Exception as e:
            self.fail(f"NPC 선택 및 대화 실패: {e}")
    
    def test_04_question_answering_flow(self):
        """문제 답변 플로우 테스트"""
        print("\n🧪 문제 답변 플로우 테스트...")
        
        try:
            # 게임 화면까지 진행
            self._start_game_to_question()
            
            # 문제 로딩 대기
            time.sleep(3)
            
            # 선택지 확인
            options = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "option-item"))
            )
            self.assertEqual(len(options), 4, "4개의 선택지가 있어야 합니다")
            
            # 첫 번째 선택지 클릭
            options[0].click()
            
            # 선택지가 선택되었는지 확인
            self.assertIn("selected", options[0].get_attribute("class"))
            
            # 답안 제출 버튼 활성화 확인
            submit_btn = self.driver.find_element(By.ID, "submit-answer-btn")
            self.assertFalse(submit_btn.get_attribute("disabled"))
            
            # 답안 제출
            submit_btn.click()
            
            # 결과 화면으로 이동 확인 (시간이 걸릴 수 있음)
            result_screen = self.wait.until(
                EC.visibility_of_element_located((By.ID, "result-screen"))
            )
            self.assertTrue(result_screen.is_displayed())
            
            print("✅ 문제 답변 플로우 성공")
            
        except TimeoutException:
            self.fail("문제 답변 플로우 시간 초과")
        except Exception as e:
            self.fail(f"문제 답변 플로우 실패: {e}")
    
    def test_05_hint_system(self):
        """힌트 시스템 테스트"""
        print("\n🧪 힌트 시스템 테스트...")
        
        try:
            # 게임 화면까지 진행
            self._start_game_to_question()
            
            # 문제 로딩 대기
            time.sleep(3)
            
            # 힌트 버튼 클릭
            hint_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "hint-btn"))
            )
            hint_btn.click()
            
            # 힌트 표시 확인 (NPC 대화 또는 알림)
            time.sleep(2)
            
            # 힌트 사용 후 버튼 상태 변경 확인
            hint_text = hint_btn.text
            self.assertIn("2", hint_text, "힌트 개수가 감소해야 합니다")
            
            print("✅ 힌트 시스템 성공")
            
        except TimeoutException:
            self.fail("힌트 시스템 시간 초과")
        except Exception as e:
            self.fail(f"힌트 시스템 실패: {e}")
    
    def test_06_aws_advisor_modal(self):
        """AWS 조언자 모달 테스트"""
        print("\n🧪 AWS 조언자 모달 테스트...")
        
        try:
            self.driver.get(self.base_url)
            
            # 로딩 완료 대기
            self.wait.until(
                EC.invisibility_of_element_located((By.ID, "loading-screen"))
            )
            
            # AWS 조언자 버튼 클릭
            advisor_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "aws-advisor-btn"))
            )
            advisor_btn.click()
            
            # 모달 표시 확인
            modal = self.wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "aws-advisor-modal"))
            )
            self.assertTrue(modal.is_displayed())
            
            # 탭 전환 테스트
            faq_tab = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-tab='faq']"))
            )
            faq_tab.click()
            
            # FAQ 탭 내용 확인
            faq_content = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-tab='faq'].advisor-tab-content"))
            )
            self.assertTrue(faq_content.is_displayed())
            
            # 모달 닫기
            close_btn = self.driver.find_element(By.CLASS_NAME, "modal-close-btn")
            close_btn.click()
            
            # 모달이 닫혔는지 확인
            time.sleep(1)
            self.assertFalse(modal.is_displayed())
            
            print("✅ AWS 조언자 모달 성공")
            
        except TimeoutException:
            self.fail("AWS 조언자 모달 시간 초과")
        except Exception as e:
            self.fail(f"AWS 조언자 모달 실패: {e}")
    
    def test_07_level_system_integration(self):
        """레벨 시스템 통합 테스트"""
        print("\n🧪 레벨 시스템 통합 테스트...")
        
        try:
            # 게임 완료까지 진행
            self._complete_one_question()
            
            # 사용자 통계 확인
            user_score = self.driver.find_element(By.ID, "user-score")
            user_level = self.driver.find_element(By.ID, "user-level")
            
            # 점수가 0보다 큰지 확인 (정답인 경우)
            score_text = user_score.text.replace(',', '')
            if score_text.isdigit():
                self.assertGreater(int(score_text), 0, "점수가 증가해야 합니다")
            
            # 레벨이 표시되는지 확인
            level_text = user_level.text
            self.assertTrue(level_text.isdigit(), "레벨이 숫자로 표시되어야 합니다")
            
            print("✅ 레벨 시스템 통합 성공")
            
        except TimeoutException:
            self.fail("레벨 시스템 통합 시간 초과")
        except Exception as e:
            self.fail(f"레벨 시스템 통합 실패: {e}")
    
    def test_08_performance_monitoring(self):
        """성능 모니터링 테스트"""
        print("\n🧪 성능 모니터링 테스트...")
        
        try:
            # 성능 대시보드 페이지 로드
            dashboard_url = f"{self.base_url}/performance_dashboard.html"
            self.driver.get(dashboard_url)
            
            # 대시보드 로딩 확인
            dashboard_header = self.wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "dashboard-header"))
            )
            self.assertTrue(dashboard_header.is_displayed())
            
            # 모니터링 시작 버튼 클릭
            start_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '모니터링 시작')]"))
            )
            start_btn.click()
            
            # 상태 표시기 활성화 확인
            time.sleep(2)
            status_indicator = self.driver.find_element(By.ID, "monitoring-status")
            self.assertIn("active", status_indicator.get_attribute("class"))
            
            # 메트릭 새로고침
            refresh_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '새로고침')]")
            refresh_btn.click()
            
            time.sleep(2)
            
            print("✅ 성능 모니터링 성공")
            
        except TimeoutException:
            self.fail("성능 모니터링 시간 초과")
        except Exception as e:
            self.fail(f"성능 모니터링 실패: {e}")
    
    def test_09_api_endpoint_connectivity(self):
        """API 엔드포인트 연결성 테스트"""
        print("\n🧪 API 엔드포인트 연결성 테스트...")
        
        if self.api_url == 'https://your-api-gateway-url/dev':
            self.skipTest("실제 API URL이 설정되지 않았습니다.")
        
        try:
            # 힌트 API 테스트
            hint_payload = {
                "action": "get_hint",
                "questionData": {
                    "category": "EC2",
                    "difficulty": "medium",
                    "scenario": {
                        "description": "테스트 시나리오"
                    },
                    "question": "테스트 질문"
                },
                "npcId": "alex_ceo",
                "hintLevel": 1
            }
            
            response = requests.post(
                f"{self.api_url}/hints",
                json=hint_payload,
                timeout=10
            )
            
            self.assertEqual(response.status_code, 200, "API 응답 상태 코드가 200이어야 합니다")
            
            response_data = response.json()
            self.assertIn("hint", response_data, "응답에 힌트가 포함되어야 합니다")
            
            print("✅ API 엔드포인트 연결성 성공")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"API 요청 실패: {e}")
        except Exception as e:
            self.fail(f"API 엔드포인트 테스트 실패: {e}")
    
    def test_10_mobile_responsiveness(self):
        """모바일 반응형 테스트"""
        print("\n🧪 모바일 반응형 테스트...")
        
        try:
            # 모바일 화면 크기로 변경
            self.driver.set_window_size(375, 667)  # iPhone 6/7/8 크기
            
            self.driver.get(self.base_url)
            
            # 로딩 완료 대기
            self.wait.until(
                EC.invisibility_of_element_located((By.ID, "loading-screen"))
            )
            
            # 모바일에서 요소들이 제대로 표시되는지 확인
            welcome_screen = self.wait.until(
                EC.visibility_of_element_located((By.ID, "welcome-screen"))
            )
            self.assertTrue(welcome_screen.is_displayed())
            
            # 사용자 통계가 모바일에서도 보이는지 확인
            user_stats = self.driver.find_element(By.CLASS_NAME, "user-stats")
            self.assertTrue(user_stats.is_displayed())
            
            # 화면 크기 복원
            self.driver.set_window_size(1920, 1080)
            
            print("✅ 모바일 반응형 성공")
            
        except TimeoutException:
            self.fail("모바일 반응형 시간 초과")
        except Exception as e:
            self.fail(f"모바일 반응형 실패: {e}")
    
    # Helper Methods
    def _start_game_to_npc_selection(self):
        """게임을 NPC 선택 화면까지 진행"""
        self.driver.get(self.base_url)
        
        self.wait.until(
            EC.invisibility_of_element_located((By.ID, "loading-screen"))
        )
        
        username_input = self.wait.until(
            EC.element_to_be_clickable((By.ID, "username-input"))
        )
        username_input.clear()
        username_input.send_keys("TestUser")
        
        mode_card = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-mode='practice']"))
        )
        mode_card.click()
        
        start_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "start-game-btn"))
        )
        start_button.click()
        
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "npc-selection-screen"))
        )
    
    def _start_game_to_question(self):
        """게임을 문제 화면까지 진행"""
        self._start_game_to_npc_selection()
        
        npc_card = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-npc='alex_ceo']"))
        )
        npc_card.click()
        
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "game-screen"))
        )
        
        # 대화 건너뛰기
        time.sleep(2)
        try:
            skip_btn = self.driver.find_element(By.ID, "skip-dialogue-btn")
            if skip_btn.is_displayed():
                skip_btn.click()
        except:
            pass
    
    def _complete_one_question(self):
        """한 문제를 완료까지 진행"""
        self._start_game_to_question()
        
        time.sleep(3)
        
        options = self.wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "option-item"))
        )
        options[0].click()
        
        submit_btn = self.driver.find_element(By.ID, "submit-answer-btn")
        submit_btn.click()
        
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "result-screen"))
        )


class APITestSuite(unittest.TestCase):
    """API 전용 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.api_url = os.getenv('TEST_API_URL', 'https://your-api-gateway-url/dev')
        
        if self.api_url == 'https://your-api-gateway-url/dev':
            self.skipTest("실제 API URL이 설정되지 않았습니다.")
    
    def test_hint_api_response_structure(self):
        """힌트 API 응답 구조 테스트"""
        payload = {
            "action": "get_hint",
            "questionData": {
                "category": "EC2",
                "difficulty": "medium",
                "scenario": {"description": "테스트"},
                "question": "테스트 질문"
            },
            "npcId": "alex_ceo",
            "hintLevel": 1
        }
        
        response = requests.post(f"{self.api_url}/hints", json=payload, timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 필수 필드 확인
        required_fields = ['hint', 'source', 'npc_id', 'hint_level', 'success']
        for field in required_fields:
            self.assertIn(field, data, f"응답에 {field} 필드가 있어야 합니다")
    
    def test_explanation_api_response_structure(self):
        """설명 API 응답 구조 테스트"""
        payload = {
            "action": "get_explanation",
            "serviceName": "EC2",
            "context": "웹 애플리케이션 호스팅"
        }
        
        response = requests.post(f"{self.api_url}/hints", json=payload, timeout=10)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 필수 필드 확인
        required_fields = ['explanation', 'service', 'source', 'success']
        for field in required_fields:
            self.assertIn(field, data, f"응답에 {field} 필드가 있어야 합니다")


def run_integration_tests():
    """통합 테스트 실행"""
    print("🚀 AWS Problem Solver Game - 통합 테스트 시작")
    print("=" * 60)
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 통합 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTestSuite))
    
    # API 테스트 추가 (환경 변수가 설정된 경우에만)
    if os.getenv('TEST_API_URL') and os.getenv('TEST_API_URL') != 'https://your-api-gateway-url/dev':
        suite.addTests(loader.loadTestsFromTestCase(APITestSuite))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("🏁 통합 테스트 완료")
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n💥 오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 환경 변수 설정 안내
    print("환경 변수 설정:")
    print(f"TEST_BASE_URL: {os.getenv('TEST_BASE_URL', 'http://localhost:8000')} (기본값)")
    print(f"TEST_API_URL: {os.getenv('TEST_API_URL', '설정되지 않음')}")
    print()
    
    # 필수 도구 확인
    try:
        import selenium
        print("✅ Selenium 설치됨")
    except ImportError:
        print("❌ Selenium이 설치되지 않았습니다: pip install selenium")
        sys.exit(1)
    
    try:
        import requests
        print("✅ Requests 설치됨")
    except ImportError:
        print("❌ Requests가 설치되지 않았습니다: pip install requests")
        sys.exit(1)
    
    print()
    
    # 테스트 실행
    success = run_integration_tests()
    sys.exit(0 if success else 1)
