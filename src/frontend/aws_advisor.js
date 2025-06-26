/**
 * AWS Problem Solver Game - AWS Advisor System
 * Amazon Q CLI를 활용한 실시간 AWS 조언 시스템
 */

class AWSAdvisor {
    constructor(gameManager) {
        this.gameManager = gameManager;
        this.advisorModal = null;
        this.currentExplanation = null;
        
        // AWS 서비스 카테고리 정의
        this.serviceCategories = {
            'Compute': ['EC2', 'Lambda', 'ECS', 'EKS', 'Fargate', 'Batch'],
            'Storage': ['S3', 'EBS', 'EFS', 'FSx', 'Glacier', 'Storage Gateway'],
            'Database': ['RDS', 'DynamoDB', 'ElastiCache', 'Neptune', 'DocumentDB', 'Redshift'],
            'Networking': ['VPC', 'CloudFront', 'Route 53', 'API Gateway', 'Direct Connect', 'VPN'],
            'Security': ['IAM', 'Cognito', 'KMS', 'Secrets Manager', 'WAF', 'Shield'],
            'Analytics': ['Athena', 'EMR', 'Kinesis', 'QuickSight', 'Glue', 'Data Pipeline'],
            'Machine Learning': ['SageMaker', 'Rekognition', 'Comprehend', 'Translate', 'Polly', 'Lex'],
            'Developer Tools': ['CodeCommit', 'CodeBuild', 'CodeDeploy', 'CodePipeline', 'Cloud9', 'X-Ray'],
            'Management': ['CloudWatch', 'CloudTrail', 'Config', 'Systems Manager', 'CloudFormation', 'CDK']
        };
        
        // 자주 묻는 질문 템플릿
        this.faqTemplates = [
            "언제 {service}를 사용해야 하나요?",
            "{service}의 주요 장점은 무엇인가요?",
            "{service} 비용을 최적화하는 방법은?",
            "{service}와 다른 서비스의 차이점은?",
            "{service} 보안 모범 사례는?",
            "{service} 성능 최적화 방법은?",
            "{service} 모니터링 방법은?",
            "{service} 장애 대응 방법은?"
        ];
        
        this.init();
    }
    
    init() {
        this.createAdvisorButton();
        this.setupEventListeners();
    }
    
    createAdvisorButton() {
        // AWS 조언자 버튼을 헤더에 추가
        const headerRight = document.querySelector('.header-right');
        if (headerRight) {
            const advisorBtn = document.createElement('button');
            advisorBtn.id = 'aws-advisor-btn';
            advisorBtn.className = 'advisor-btn';
            advisorBtn.innerHTML = '<i class="fab fa-aws"></i>';
            advisorBtn.title = 'AWS 조언자';
            
            headerRight.insertBefore(advisorBtn, headerRight.querySelector('.settings-btn'));
        }
    }
    
    setupEventListeners() {
        // AWS 조언자 버튼 클릭
        document.addEventListener('click', (e) => {
            if (e.target.closest('#aws-advisor-btn')) {
                this.showAdvisorModal();
            }
        });
    }
    
    showAdvisorModal() {
        if (this.advisorModal) {
            this.advisorModal.classList.add('show');
            return;
        }
        
        this.advisorModal = document.createElement('div');
        this.advisorModal.className = 'aws-advisor-modal';
        this.advisorModal.innerHTML = this.generateAdvisorModalHTML();
        
        document.body.appendChild(this.advisorModal);
        
        // Show modal
        setTimeout(() => this.advisorModal.classList.add('show'), 100);
        
        // Setup modal event listeners
        this.setupModalEventListeners();
    }
    
    generateAdvisorModalHTML() {
        const serviceOptions = this.generateServiceOptions();
        const faqOptions = this.generateFAQOptions();
        
        return `
            <div class="aws-advisor-content">
                <div class="advisor-header">
                    <div class="advisor-title">
                        <i class="fab fa-aws"></i>
                        <h2>AWS 조언자</h2>
                    </div>
                    <button class="modal-close-btn" data-action="close">&times;</button>
                </div>
                
                <div class="advisor-tabs">
                    <button class="advisor-tab active" data-tab="services">서비스 설명</button>
                    <button class="advisor-tab" data-tab="faq">자주 묻는 질문</button>
                    <button class="advisor-tab" data-tab="best-practices">모범 사례</button>
                    <button class="advisor-tab" data-tab="troubleshooting">문제 해결</button>
                </div>
                
                <div class="advisor-content-area">
                    <!-- 서비스 설명 탭 -->
                    <div class="advisor-tab-content active" data-tab="services">
                        <div class="service-search">
                            <input type="text" id="service-search" placeholder="AWS 서비스 검색 (예: EC2, S3, Lambda...)">
                            <button class="search-btn" data-action="search-service">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                        
                        <div class="service-categories">
                            <h4>서비스 카테고리</h4>
                            ${this.generateServiceCategoriesHTML()}
                        </div>
                        
                        <div class="popular-services">
                            <h4>인기 서비스</h4>
                            <div class="service-grid">
                                ${this.generatePopularServicesHTML()}
                            </div>
                        </div>
                    </div>
                    
                    <!-- FAQ 탭 -->
                    <div class="advisor-tab-content" data-tab="faq">
                        <div class="faq-search">
                            <input type="text" id="faq-search" placeholder="질문을 입력하세요...">
                            <button class="search-btn" data-action="search-faq">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                        
                        <div class="faq-categories">
                            <h4>자주 묻는 질문</h4>
                            ${faqOptions}
                        </div>
                    </div>
                    
                    <!-- 모범 사례 탭 -->
                    <div class="advisor-tab-content" data-tab="best-practices">
                        <div class="best-practices-content">
                            <h4>AWS 모범 사례</h4>
                            ${this.generateBestPracticesHTML()}
                        </div>
                    </div>
                    
                    <!-- 문제 해결 탭 -->
                    <div class="advisor-tab-content" data-tab="troubleshooting">
                        <div class="troubleshooting-content">
                            <h4>일반적인 문제 해결</h4>
                            ${this.generateTroubleshootingHTML()}
                        </div>
                    </div>
                </div>
                
                <div class="advisor-result" id="advisor-result" style="display: none;">
                    <div class="result-header">
                        <h3 id="result-title">결과</h3>
                        <button class="clear-result-btn" data-action="clear-result">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="result-content" id="result-content">
                        <!-- 결과 내용이 여기에 표시됩니다 -->
                    </div>
                </div>
            </div>
        `;
    }
    
    generateServiceCategoriesHTML() {
        let html = '<div class="category-grid">';
        
        for (const [category, services] of Object.entries(this.serviceCategories)) {
            html += `
                <div class="category-item" data-category="${category}">
                    <h5>${category}</h5>
                    <div class="service-list">
                        ${services.slice(0, 3).map(service => 
                            `<span class="service-tag" data-service="${service}">${service}</span>`
                        ).join('')}
                        ${services.length > 3 ? `<span class="more-services">+${services.length - 3}</span>` : ''}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    generatePopularServicesHTML() {
        const popularServices = ['EC2', 'S3', 'Lambda', 'RDS', 'VPC', 'IAM', 'CloudWatch', 'API Gateway'];
        
        return popularServices.map(service => `
            <div class="service-card" data-service="${service}">
                <div class="service-icon">
                    <i class="fab fa-aws"></i>
                </div>
                <h5>${service}</h5>
                <p>클릭하여 설명 보기</p>
            </div>
        `).join('');
    }
    
    generateServiceOptions() {
        const allServices = Object.values(this.serviceCategories).flat();
        return allServices.map(service => 
            `<option value="${service}">${service}</option>`
        ).join('');
    }
    
    generateFAQOptions() {
        const commonQuestions = [
            "AWS 비용을 최적화하는 방법은?",
            "고가용성 아키텍처 설계 방법은?",
            "AWS 보안 모범 사례는?",
            "서버리스 vs 컨테이너 언제 사용하나요?",
            "데이터베이스 선택 가이드",
            "모니터링 및 로깅 전략",
            "재해 복구 계획 수립 방법",
            "마이그레이션 전략 및 도구"
        ];
        
        return `
            <div class="faq-list">
                ${commonQuestions.map(question => `
                    <div class="faq-item" data-question="${question}">
                        <i class="fas fa-question-circle"></i>
                        <span>${question}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    generateBestPracticesHTML() {
        const bestPractices = [
            {
                title: "보안 모범 사례",
                items: ["IAM 최소 권한 원칙", "MFA 활성화", "정기적인 보안 감사", "암호화 사용"]
            },
            {
                title: "비용 최적화",
                items: ["Reserved Instance 활용", "Auto Scaling 구성", "불필요한 리소스 정리", "비용 모니터링"]
            },
            {
                title: "성능 최적화",
                items: ["적절한 인스턴스 타입 선택", "캐싱 전략", "CDN 활용", "데이터베이스 최적화"]
            },
            {
                title: "운영 우수성",
                items: ["Infrastructure as Code", "자동화", "모니터링", "문서화"]
            }
        ];
        
        return bestPractices.map(practice => `
            <div class="best-practice-section">
                <h5>${practice.title}</h5>
                <ul>
                    ${practice.items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `).join('');
    }
    
    generateTroubleshootingHTML() {
        const troubleshooting = [
            {
                problem: "EC2 인스턴스 연결 불가",
                solutions: ["보안 그룹 확인", "키 페어 확인", "네트워크 ACL 확인", "인스턴스 상태 확인"]
            },
            {
                problem: "S3 액세스 거부",
                solutions: ["버킷 정책 확인", "IAM 권한 확인", "CORS 설정 확인", "퍼블릭 액세스 설정 확인"]
            },
            {
                problem: "Lambda 함수 타임아웃",
                solutions: ["타임아웃 설정 증가", "메모리 할당 조정", "코드 최적화", "외부 의존성 확인"]
            },
            {
                problem: "RDS 연결 실패",
                solutions: ["보안 그룹 확인", "서브넷 그룹 확인", "엔드포인트 확인", "자격 증명 확인"]
            }
        ];
        
        return troubleshooting.map(item => `
            <div class="troubleshooting-section">
                <h5><i class="fas fa-exclamation-triangle"></i> ${item.problem}</h5>
                <ul class="solution-list">
                    ${item.solutions.map(solution => `<li>${solution}</li>`).join('')}
                </ul>
            </div>
        `).join('');
    }
    
    setupModalEventListeners() {
        this.advisorModal.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            
            switch (action) {
                case 'close':
                    this.closeAdvisorModal();
                    break;
                case 'search-service':
                    this.searchService();
                    break;
                case 'search-faq':
                    this.searchFAQ();
                    break;
                case 'clear-result':
                    this.clearResult();
                    break;
            }
            
            // 탭 전환
            if (e.target.classList.contains('advisor-tab')) {
                this.switchTab(e.target.dataset.tab);
            }
            
            // 서비스 클릭
            if (e.target.closest('.service-card') || e.target.classList.contains('service-tag')) {
                const service = e.target.dataset.service || e.target.closest('.service-card').dataset.service;
                this.explainService(service);
            }
            
            // FAQ 클릭
            if (e.target.closest('.faq-item')) {
                const question = e.target.closest('.faq-item').dataset.question;
                this.answerFAQ(question);
            }
            
            // 카테고리 클릭
            if (e.target.closest('.category-item')) {
                const category = e.target.closest('.category-item').dataset.category;
                this.showCategoryServices(category);
            }
        });
        
        // 검색 입력 엔터키 처리
        this.advisorModal.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                if (e.target.id === 'service-search') {
                    this.searchService();
                } else if (e.target.id === 'faq-search') {
                    this.searchFAQ();
                }
            }
        });
        
        // 모달 외부 클릭 시 닫기
        this.advisorModal.addEventListener('click', (e) => {
            if (e.target === this.advisorModal) {
                this.closeAdvisorModal();
            }
        });
    }
    
    switchTab(tabName) {
        // 탭 버튼 활성화
        this.advisorModal.querySelectorAll('.advisor-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        this.advisorModal.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // 탭 콘텐츠 표시
        this.advisorModal.querySelectorAll('.advisor-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        this.advisorModal.querySelector(`.advisor-tab-content[data-tab="${tabName}"]`).classList.add('active');
    }
    
    async searchService() {
        const searchInput = this.advisorModal.querySelector('#service-search');
        const serviceName = searchInput.value.trim();
        
        if (!serviceName) {
            this.showNotification('서비스 이름을 입력해주세요.', 'warning');
            return;
        }
        
        await this.explainService(serviceName);
    }
    
    async searchFAQ() {
        const searchInput = this.advisorModal.querySelector('#faq-search');
        const question = searchInput.value.trim();
        
        if (!question) {
            this.showNotification('질문을 입력해주세요.', 'warning');
            return;
        }
        
        await this.answerFAQ(question);
    }
    
    async explainService(serviceName) {
        this.showLoading();
        
        try {
            const explanation = await this.getServiceExplanation(serviceName);
            this.showResult(`${serviceName} 서비스 설명`, explanation);
        } catch (error) {
            console.error('Error explaining service:', error);
            this.showResult(`${serviceName} 서비스 설명`, this.getFallbackServiceExplanation(serviceName));
        }
    }
    
    async answerFAQ(question) {
        this.showLoading();
        
        try {
            const answer = await this.getFAQAnswer(question);
            this.showResult('FAQ 답변', answer);
        } catch (error) {
            console.error('Error answering FAQ:', error);
            this.showResult('FAQ 답변', this.getFallbackFAQAnswer(question));
        }
    }
    
    async getServiceExplanation(serviceName) {
        const requestData = {
            action: 'get_explanation',
            serviceName: serviceName,
            context: this.gameManager.currentQuestion ? 
                `현재 문제 컨텍스트: ${this.gameManager.currentQuestion.scenario?.description || ''}` : ''
        };
        
        const response = await fetch(`${this.gameManager.apiBaseUrl}/hints`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result.explanation || this.getFallbackServiceExplanation(serviceName);
    }
    
    getFallbackServiceExplanation(serviceName) {
        const explanations = {
            'EC2': `
**Amazon EC2 (Elastic Compute Cloud)**

**개요**
Amazon EC2는 클라우드에서 안전하고 크기 조정 가능한 컴퓨팅 파워를 제공하는 웹 서비스입니다.

**주요 기능**
• 다양한 인스턴스 타입 (범용, 컴퓨팅 최적화, 메모리 최적화 등)
• Auto Scaling으로 자동 확장/축소
• Elastic Load Balancing으로 트래픽 분산
• EBS 볼륨으로 영구 스토리지 제공

**사용 사례**
• 웹 애플리케이션 및 웹 서비스 호스팅
• 고성능 컴퓨팅 (HPC) 애플리케이션
• 개발 및 테스트 환경

**모범 사례**
• 적절한 인스턴스 타입 선택
• 보안 그룹으로 네트워크 보안 설정
• 정기적인 AMI 백업
• Reserved Instance로 비용 절약
            `,
            'S3': `
**Amazon S3 (Simple Storage Service)**

**개요**
Amazon S3는 업계 최고의 확장성, 데이터 가용성, 보안 및 성능을 제공하는 객체 스토리지 서비스입니다.

**주요 기능**
• 무제한 스토리지 용량
• 11 9's (99.999999999%) 내구성
• 다양한 스토리지 클래스 (Standard, IA, Glacier 등)
• 버전 관리 및 라이프사이클 정책

**사용 사례**
• 정적 웹사이트 호스팅
• 데이터 백업 및 아카이브
• 빅데이터 분석을 위한 데이터 레이크
• CDN 원본 스토리지

**모범 사례**
• 적절한 스토리지 클래스 선택으로 비용 최적화
• 버킷 정책과 IAM으로 액세스 제어
• 서버 측 암호화 활성화
• CloudTrail로 API 호출 로깅
            `,
            'Lambda': `
**AWS Lambda**

**개요**
AWS Lambda는 서버를 프로비저닝하거나 관리하지 않고도 코드를 실행할 수 있는 서버리스 컴퓨팅 서비스입니다.

**주요 기능**
• 자동 스케일링 (0에서 수천 개의 동시 실행)
• 이벤트 기반 실행
• 다양한 런타임 지원 (Python, Node.js, Java 등)
• 내장 모니터링 및 로깅

**사용 사례**
• API 백엔드 (API Gateway와 함께)
• 실시간 파일 처리
• 데이터 변환 및 ETL
• IoT 백엔드

**모범 사례**
• 함수 크기 최소화 (콜드 스타트 최적화)
• 환경 변수로 설정 관리
• 적절한 메모리 할당
• 데드 레터 큐 설정
            `
        };
        
        return explanations[serviceName.toUpperCase()] || `
**${serviceName}**

죄송합니다. ${serviceName}에 대한 상세 정보를 현재 제공할 수 없습니다.
AWS 공식 문서를 참조하시거나 다른 서비스를 검색해보세요.

**추천 서비스**
• EC2 - 가상 서버
• S3 - 객체 스토리지  
• Lambda - 서버리스 컴퓨팅
• RDS - 관리형 데이터베이스
        `;
    }
    
    async getFAQAnswer(question) {
        // 실제로는 Amazon Q CLI를 통해 답변을 받아올 수 있습니다
        return this.getFallbackFAQAnswer(question);
    }
    
    getFallbackFAQAnswer(question) {
        const faqAnswers = {
            "AWS 비용을 최적화하는 방법은?": `
**AWS 비용 최적화 전략**

1. **Right Sizing**
   • 실제 사용량에 맞는 인스턴스 크기 선택
   • CloudWatch 메트릭을 통한 사용률 모니터링

2. **Reserved Instance & Savings Plans**
   • 1년 또는 3년 약정으로 최대 75% 할인
   • 예측 가능한 워크로드에 적합

3. **Spot Instance 활용**
   • 최대 90% 할인된 가격
   • 중단 가능한 워크로드에 적합

4. **자동화 및 스케줄링**
   • Auto Scaling으로 필요시에만 리소스 사용
   • 개발/테스트 환경 자동 종료

5. **스토리지 최적화**
   • S3 Intelligent Tiering 사용
   • 불필요한 스냅샷 및 볼륨 정리
            `,
            "고가용성 아키텍처 설계 방법은?": `
**고가용성 아키텍처 설계 원칙**

1. **다중 AZ 배포**
   • 최소 2개 이상의 가용 영역 사용
   • 지역적 장애에 대한 복원력 확보

2. **로드 밸런싱**
   • Application Load Balancer 사용
   • 헬스 체크로 비정상 인스턴스 자동 제외

3. **Auto Scaling**
   • 트래픽에 따른 자동 확장/축소
   • 최소/최대 인스턴스 수 설정

4. **데이터베이스 고가용성**
   • RDS Multi-AZ 배포
   • Read Replica로 읽기 성능 향상

5. **모니터링 및 알림**
   • CloudWatch로 실시간 모니터링
   • SNS로 장애 알림 설정
            `
        };
        
        return faqAnswers[question] || `
**질문에 대한 답변**

죄송합니다. "${question}"에 대한 구체적인 답변을 현재 제공할 수 없습니다.

**도움이 될 만한 리소스:**
• AWS 공식 문서
• AWS Well-Architected Framework
• AWS 솔루션 아키텍처 센터
• AWS 기술 블로그

더 구체적인 질문이나 특정 서비스에 대한 질문을 해보세요.
        `;
    }
    
    showCategoryServices(category) {
        const services = this.serviceCategories[category] || [];
        const serviceList = services.map(service => 
            `<div class="service-card" data-service="${service}">
                <div class="service-icon"><i class="fab fa-aws"></i></div>
                <h5>${service}</h5>
                <p>클릭하여 설명 보기</p>
            </div>`
        ).join('');
        
        this.showResult(`${category} 서비스`, `
            <div class="service-grid">
                ${serviceList}
            </div>
        `);
    }
    
    showResult(title, content) {
        const resultArea = this.advisorModal.querySelector('#advisor-result');
        const resultTitle = this.advisorModal.querySelector('#result-title');
        const resultContent = this.advisorModal.querySelector('#result-content');
        
        resultTitle.textContent = title;
        resultContent.innerHTML = content;
        resultArea.style.display = 'block';
        
        // 결과 영역으로 스크롤
        resultArea.scrollIntoView({ behavior: 'smooth' });
    }
    
    clearResult() {
        const resultArea = this.advisorModal.querySelector('#advisor-result');
        resultArea.style.display = 'none';
    }
    
    showLoading() {
        this.showResult('로딩 중...', `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <p>AWS 조언자가 답변을 준비하고 있습니다...</p>
            </div>
        `);
    }
    
    closeAdvisorModal() {
        if (this.advisorModal) {
            this.advisorModal.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(this.advisorModal)) {
                    document.body.removeChild(this.advisorModal);
                    this.advisorModal = null;
                }
            }, 300);
        }
    }
    
    showNotification(message, type) {
        if (this.gameManager && this.gameManager.showNotification) {
            this.gameManager.showNotification(message, type);
        } else {
            alert(message);
        }
    }
}

// Export for use in other modules
window.AWSAdvisor = AWSAdvisor;
