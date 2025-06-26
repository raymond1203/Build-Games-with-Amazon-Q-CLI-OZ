/**
 * AWS Problem Solver Game - NPC System
 * Handles NPC interactions, dialogues, and character-specific behaviors
 */

class NPCSystem {
    constructor(gameManager) {
        this.gameManager = gameManager;
        this.currentDialogueSession = null;
        this.dialogueQueue = [];
        this.isTyping = false;
        this.typingSpeed = 50; // milliseconds per character
        
        this.npcData = {
            alex_ceo: {
                name: "Alex",
                title: "스타트업 CEO",
                personality: "energetic",
                greetings: [
                    "안녕하세요! 저는 TechStart의 CEO Alex입니다. 우리 서비스가 갑자기 인기를 끌면서 기술적인 문제들이 생겼어요.",
                    "시간이 정말 중요해요! 투자자 미팅이 내일인데 이 문제를 해결해야 해요!",
                    "비용은 중요하지만 서비스가 다운되면 안 되거든요. 빠른 해결책이 필요해요!"
                ],
                correctResponses: [
                    "와! 정말 완벽한 솔루션이네요!",
                    "이거면 투자자들에게 자신있게 설명할 수 있겠어요!",
                    "비용도 절약되고 성능도 좋아지다니, 일석이조네요!",
                    "정말 감사합니다! 바로 적용해보겠어요!"
                ],
                incorrectResponses: [
                    "음... 그 방법도 좋지만 비용이 너무 많이 들 것 같아요.",
                    "확실한 해결책인지 좀 더 생각해봐야겠어요.",
                    "다른 더 효율적인 방법은 없을까요?",
                    "투자자들이 납득할 만한 솔루션이 필요한데..."
                ],
                hintStyles: [
                    "시간이 없어요! {hint} 빨리 해결해봅시다!",
                    "비즈니스 관점에서 보면... {hint} 이 방법이 가장 효과적일 거예요.",
                    "투자자들도 이해할 수 있는 솔루션이 필요해요. {hint}"
                ]
            },
            sarah_analyst: {
                name: "Sarah",
                title: "데이터 분석가",
                personality: "analytical",
                greetings: [
                    "안녕하세요, 데이터 분석가 Sarah입니다. 대용량 데이터 처리와 분석에 관련된 AWS 솔루션에 대해 궁금한 점이 있어요.",
                    "데이터 파이프라인에서 병목이 발생하고 있어서 정확하고 효율적인 방법을 찾고 있습니다.",
                    "매일 처리해야 하는 데이터량이 계속 증가하고 있어서 더 체계적인 접근이 필요해요."
                ],
                correctResponses: [
                    "완벽한 분석이네요! 이 솔루션이면 처리 시간을 크게 단축할 수 있겠어요.",
                    "데이터 품질도 향상되고 비용도 절약되는 훌륭한 방법이네요!",
                    "이런 체계적인 접근 방식이 바로 제가 찾던 거예요!",
                    "정말 감사합니다. 이제 더 정확한 분석이 가능하겠어요!"
                ],
                incorrectResponses: [
                    "음... 그 방법은 데이터 정합성에 문제가 있을 수 있어요.",
                    "처리 시간은 단축되겠지만 정확도가 떨어질 것 같은데요.",
                    "좀 더 체계적인 접근이 필요할 것 같아요.",
                    "데이터 품질 관리 측면에서 다시 검토해봐야겠어요."
                ],
                hintStyles: [
                    "차근차근 생각해보면... {hint} 이런 접근이 좋을 것 같아요.",
                    "데이터 관점에서 분석하면 {hint} 이 방법이 가장 효율적입니다.",
                    "통계적으로 보면... {hint} 이런 패턴을 고려해보세요."
                ]
            },
            mike_security: {
                name: "Mike",
                title: "보안 담당자",
                personality: "cautious",
                greetings: [
                    "보안 담당자 Mike입니다. 클라우드 보안을 강화하고 싶은데, AWS의 보안 서비스들에 대해 조언을 구하고 싶습니다.",
                    "최근 보안 감사에서 몇 가지 취약점이 발견되었어요. 규제 준수 요구사항을 만족해야 하는 상황입니다.",
                    "제로 트러스트 보안 모델을 구현해야 해요. 보안은 타협할 수 없는 영역이라고 생각합니다."
                ],
                correctResponses: [
                    "완벽한 보안 설계네요! 이렇게 하면 규제 요구사항도 만족할 수 있겠어요.",
                    "다층 보안 접근 방식이 정말 훌륭합니다!",
                    "이 솔루션이면 보안 감사도 무사히 통과할 수 있겠네요!",
                    "정말 감사합니다. 이제 안심하고 운영할 수 있겠어요!"
                ],
                incorrectResponses: [
                    "그 방법은 보안상 위험할 수 있어요.",
                    "규제 요구사항을 만족하지 못할 것 같은데요.",
                    "좀 더 보안을 강화할 수 있는 방법은 없을까요?",
                    "보안과 편의성 사이에서 보안을 우선해야 합니다."
                ],
                hintStyles: [
                    "안전을 위해서는... {hint} 이 방법을 권장합니다.",
                    "보안 관점에서 보면 {hint} 이런 접근이 필요해요.",
                    "규제 준수를 위해서는... {hint} 이 부분을 고려해야 합니다."
                ]
            },
            jenny_developer: {
                name: "Jenny",
                title: "풀스택 개발자",
                personality: "curious",
                greetings: [
                    "개발자 Jenny입니다! 서버리스 아키텍처로 애플리케이션을 만들고 싶은데, 어떤 AWS 서비스들을 사용해야 할지 고민이에요.",
                    "서버 관리 없이 애플리케이션을 만들고 싶어요. 새로운 기술을 배우는 걸 좋아해서 도전해보고 싶어요!",
                    "최신 기술을 활용한 혁신적인 솔루션을 찾고 있어요. 개발에만 집중할 수 있는 환경을 만들고 싶어요."
                ],
                correctResponses: [
                    "와! 이런 방법이 있었네요! 정말 혁신적이에요!",
                    "서버리스의 진정한 장점을 활용한 완벽한 솔루션이네요!",
                    "이제 개발에만 집중할 수 있겠어요! 정말 감사해요!",
                    "바로 구현해보고 싶어요! 너무 흥미로운 접근법이에요!"
                ],
                incorrectResponses: [
                    "음... 그 방법도 좋지만 더 모던한 방식은 없을까요?",
                    "서버리스의 장점을 충분히 활용하지 못하는 것 같아요.",
                    "좀 더 자동화된 솔루션이 있을 것 같은데요.",
                    "개발자 친화적인 다른 방법을 고려해볼까요?"
                ],
                hintStyles: [
                    "힌트를 드릴게요! {hint} 이제 해결할 수 있을 거예요!",
                    "새로운 접근법을 시도해보세요. {hint} 이런 방법은 어떨까요?",
                    "개발자 관점에서 보면... {hint} 이게 가장 효율적일 것 같아요!"
                ]
            }
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Dialogue continue button
        document.getElementById('continue-dialogue-btn').addEventListener('click', () => {
            this.continueDialogue();
        });
        
        // Skip dialogue button
        document.getElementById('skip-dialogue-btn').addEventListener('click', () => {
            this.skipDialogue();
        });
    }
    
    async startNpcDialogue(npcId) {
        this.currentNpc = npcId;
        const npcData = this.npcData[npcId];
        
        if (!npcData) {
            console.error('NPC data not found:', npcId);
            return;
        }
        
        // Update NPC display
        this.updateNpcDisplay(npcData);
        
        // Start dialogue session
        this.currentDialogueSession = {
            npcId: npcId,
            phase: 'greeting',
            messageIndex: 0
        };
        
        // Show dialogue area
        document.querySelector('.npc-dialogue-area').style.display = 'block';
        
        // Start with greeting
        await this.showGreeting(npcData);
    }
    
    updateNpcDisplay(npcData) {
        const avatarElement = document.getElementById('current-npc-avatar');
        const nameElement = document.getElementById('current-npc-name');
        const titleElement = document.getElementById('current-npc-title');
        
        avatarElement.className = `npc-avatar-large ${this.currentNpc}`;
        nameElement.textContent = npcData.name;
        titleElement.textContent = npcData.title;
        
        // Update dialogue box styling
        const dialogueBox = document.querySelector('.dialogue-box');
        dialogueBox.className = `dialogue-box ${this.currentNpc}`;
    }
    
    async showGreeting(npcData) {
        const greetings = npcData.greetings;
        
        for (let i = 0; i < greetings.length; i++) {
            await this.typeMessage(greetings[i]);
            
            if (i < greetings.length - 1) {
                await this.waitForContinue();
            }
        }
        
        // After greeting, show the question
        this.hideDialogueArea();
        await this.gameManager.loadQuestion();
    }
    
    async typeMessage(message) {
        const dialogueText = document.getElementById('dialogue-text');
        const continueBtn = document.getElementById('continue-dialogue-btn');
        const skipBtn = document.getElementById('skip-dialogue-btn');
        
        this.isTyping = true;
        continueBtn.style.display = 'none';
        skipBtn.style.display = 'inline-block';
        
        dialogueText.textContent = '';
        
        for (let i = 0; i < message.length; i++) {
            if (!this.isTyping) break; // Skip was pressed
            
            dialogueText.textContent += message[i];
            await this.sleep(this.typingSpeed);
        }
        
        // Show full message if skipped
        if (!this.isTyping) {
            dialogueText.textContent = message;
        }
        
        this.isTyping = false;
        continueBtn.style.display = 'inline-block';
        skipBtn.style.display = 'none';
    }
    
    async waitForContinue() {
        return new Promise((resolve) => {
            const continueBtn = document.getElementById('continue-dialogue-btn');
            
            const handleContinue = () => {
                continueBtn.removeEventListener('click', handleContinue);
                resolve();
            };
            
            continueBtn.addEventListener('click', handleContinue);
        });
    }
    
    continueDialogue() {
        // This will be handled by the promise in waitForContinue
    }
    
    skipDialogue() {
        this.isTyping = false;
    }
    
    hideDialogueArea() {
        document.querySelector('.npc-dialogue-area').style.display = 'none';
    }
    
    async showAnswerResponse(isCorrect, questionResult) {
        if (!this.currentNpc) return;
        
        const npcData = this.npcData[this.currentNpc];
        const responses = isCorrect ? npcData.correctResponses : npcData.incorrectResponses;
        const response = this.getRandomItem(responses);
        
        // Show dialogue area again
        document.querySelector('.npc-dialogue-area').style.display = 'block';
        
        // Add personality indicator
        const personalityResponse = this.addPersonalityToResponse(response, npcData.personality, isCorrect);
        
        await this.typeMessage(personalityResponse);
        await this.sleep(2000); // Show response for 2 seconds
        
        this.hideDialogueArea();
    }
    
    addPersonalityToResponse(response, personality, isCorrect) {
        const personalityModifiers = {
            energetic: {
                correct: ["정말 빠른 해결책이네요! ", "시간 절약! ", "완벽해요! "],
                incorrect: ["음... ", "시간이 부족한데... ", "다시 생각해봐야겠어요. "]
            },
            analytical: {
                correct: ["데이터 분석 결과 ", "체계적인 접근이네요. ", "정확한 판단입니다. "],
                incorrect: ["분석해보니... ", "데이터상으로는... ", "좀 더 검토가 필요해요. "]
            },
            cautious: {
                correct: ["안전한 선택이네요. ", "보안 관점에서 완벽합니다. ", "규정에 맞는 솔루션이에요. "],
                incorrect: ["보안상 위험할 수 있어요. ", "좀 더 신중하게... ", "안전을 위해서는... "]
            },
            curious: {
                correct: ["와! 새로운 방법이네요! ", "정말 혁신적이에요! ", "이런 접근법도 있었군요! "],
                incorrect: ["흥미로운 시도지만... ", "다른 방법도 있을 것 같은데... ", "더 탐구해봐야겠어요. "]
            }
        };
        
        const modifiers = personalityModifiers[personality];
        if (modifiers) {
            const modifier = this.getRandomItem(modifiers[isCorrect ? 'correct' : 'incorrect']);
            return modifier + response;
        }
        
        return response;
    }
    
    async requestNpcHint(questionData, hintLevel) {
        if (!this.currentNpc) return null;
        
        try {
            // Show dialogue area for hint
            document.querySelector('.npc-dialogue-area').style.display = 'block';
            
            const requestData = {
                action: 'get_hint',
                sessionId: this.gameManager.currentSession?.id || 'temp_session',
                questionData: {
                    questionId: questionData.questionId,
                    category: questionData.category,
                    difficulty: questionData.difficulty,
                    scenario: questionData.scenario,
                    question: questionData.question
                },
                npcId: this.currentNpc,
                hintLevel: hintLevel
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
            
            const hintData = await response.json();
            
            // Show the hint with NPC personality
            await this.showNpcHint(hintData);
            
            return hintData;
            
        } catch (error) {
            console.error('Error requesting NPC hint:', error);
            
            // Fallback to enhanced local hint
            const npcData = this.npcData[this.currentNpc];
            const fallbackHint = this.generateEnhancedFallbackHint(questionData, npcData, hintLevel);
            await this.showNpcHint(fallbackHint);
            
            return fallbackHint;
        }
    }
    
    async showNpcHint(hintData) {
        const message = hintData.message || hintData.hint;
        
        await this.typeMessage(message);
        await this.waitForContinue();
        
        this.hideDialogueArea();
    }
    
    generateEnhancedFallbackHint(questionData, npcData, hintLevel) {
        const category = questionData.category?.toUpperCase() || 'GENERAL';
        
        // 카테고리별 상세 힌트 템플릿
        const enhancedHintTemplates = {
            'EC2': {
                1: {
                    base: "인스턴스 확장성과 로드 밸런싱을 고려해보세요.",
                    alex_ceo: "트래픽 급증에 대비한 확장 가능한 솔루션이 필요해요!",
                    sarah_analyst: "데이터를 보니 Auto Scaling이 가장 효율적일 것 같아요.",
                    mike_security: "보안을 유지하면서 확장할 수 있는 방법을 찾아보세요.",
                    jenny_developer: "서버 관리 없이 자동으로 확장되는 방법이 있어요!"
                },
                2: {
                    base: "Auto Scaling Group과 Application Load Balancer 조합을 생각해보세요.",
                    alex_ceo: "ALB와 ASG로 비용 효율적인 확장이 가능해요!",
                    sarah_analyst: "로드 밸런서 메트릭을 분석하면 최적의 설정을 찾을 수 있어요.",
                    mike_security: "보안 그룹과 함께 안전한 로드 밸런싱을 구성해보세요.",
                    jenny_developer: "코드 배포도 자동화할 수 있는 완벽한 조합이에요!"
                },
                3: {
                    base: "다중 AZ 배포와 CloudWatch 모니터링을 포함한 완전한 아키텍처를 설계해보세요.",
                    alex_ceo: "투자자들이 좋아할 고가용성 아키텍처를 만들어봅시다!",
                    sarah_analyst: "CloudWatch 대시보드로 모든 지표를 한눈에 볼 수 있어요.",
                    mike_security: "다중 AZ로 장애 복구와 보안을 동시에 확보하세요.",
                    jenny_developer: "Infrastructure as Code로 전체 스택을 관리해보세요!"
                }
            },
            'S3': {
                1: {
                    base: "스토리지 클래스와 액세스 패턴을 고려해보세요.",
                    alex_ceo: "비용 최적화를 위한 스토리지 전략이 중요해요!",
                    sarah_analyst: "액세스 패턴을 분석해서 적절한 클래스를 선택하세요.",
                    mike_security: "데이터 암호화와 접근 제어를 잊지 마세요.",
                    jenny_developer: "라이프사이클 정책으로 자동화해보세요!"
                },
                2: {
                    base: "Standard-IA, Glacier 등 적절한 스토리지 클래스를 선택해보세요.",
                    alex_ceo: "Standard-IA로 비용을 70% 절약할 수 있어요!",
                    sarah_analyst: "데이터 액세스 빈도에 따라 클래스를 분류해보세요.",
                    mike_security: "Glacier로 장기 보관하면서 규제 요구사항도 만족해요.",
                    jenny_developer: "Intelligent Tiering으로 자동 최적화가 가능해요!"
                },
                3: {
                    base: "라이프사이클 정책과 버전 관리를 포함한 완전한 스토리지 전략을 수립해보세요.",
                    alex_ceo: "완전 자동화된 스토리지 관리로 운영비를 대폭 절감해요!",
                    sarah_analyst: "버전 관리와 메트릭 분석으로 완벽한 데이터 거버넌스를 구축하세요.",
                    mike_security: "MFA Delete와 Cross-Region Replication으로 최고 수준의 보안을 확보하세요.",
                    jenny_developer: "S3 이벤트와 Lambda로 완전 자동화된 워크플로우를 만들어보세요!"
                }
            },
            'LAMBDA': {
                1: {
                    base: "서버리스 아키텍처와 이벤트 기반 처리를 고려해보세요.",
                    alex_ceo: "서버 관리 비용을 완전히 없앨 수 있어요!",
                    sarah_analyst: "이벤트 기반으로 정확한 데이터 처리가 가능해요.",
                    mike_security: "서버리스로 공격 표면을 최소화할 수 있어요.",
                    jenny_developer: "코드만 작성하면 나머지는 AWS가 알아서 해줘요!"
                },
                2: {
                    base: "Lambda와 API Gateway, DynamoDB 조합을 생각해보세요.",
                    alex_ceo: "완전 서버리스 스택으로 운영비 제로를 달성해요!",
                    sarah_analyst: "DynamoDB 스트림으로 실시간 데이터 분석이 가능해요.",
                    mike_security: "IAM 역할로 세밀한 권한 제어가 가능해요.",
                    jenny_developer: "SAM이나 CDK로 전체 스택을 코드로 관리해보세요!"
                },
                3: {
                    base: "Step Functions를 활용한 워크플로우 오케스트레이션을 포함해보세요.",
                    alex_ceo: "복잡한 비즈니스 로직도 시각적으로 관리할 수 있어요!",
                    sarah_analyst: "Step Functions으로 데이터 파이프라인을 체계적으로 구성하세요.",
                    mike_security: "각 단계별로 보안 검증을 추가할 수 있어요.",
                    jenny_developer: "에러 처리와 재시도 로직까지 완벽하게 자동화해보세요!"
                }
            },
            'RDS': {
                1: {
                    base: "데이터베이스 가용성과 백업 전략을 고려해보세요.",
                    alex_ceo: "데이터베이스 다운타임은 비즈니스에 치명적이에요!",
                    sarah_analyst: "백업과 복구 시간을 정확히 계산해보세요.",
                    mike_security: "데이터 암호화와 접근 제어가 필수예요.",
                    jenny_developer: "자동 백업으로 관리 부담을 줄여보세요!"
                },
                2: {
                    base: "Multi-AZ 배포와 Read Replica를 생각해보세요.",
                    alex_ceo: "Multi-AZ로 99.95% 가용성을 보장할 수 있어요!",
                    sarah_analyst: "Read Replica로 읽기 성능을 5배까지 향상시킬 수 있어요.",
                    mike_security: "암호화된 Read Replica로 보안과 성능을 동시에 확보하세요.",
                    jenny_developer: "Aurora Serverless로 자동 스케일링까지 가능해요!"
                },
                3: {
                    base: "자동 백업, 모니터링, 성능 최적화를 포함한 완전한 DB 솔루션을 설계해보세요.",
                    alex_ceo: "완전 자동화된 DB 관리로 DBA 비용까지 절약해요!",
                    sarah_analyst: "Performance Insights로 쿼리 성능을 실시간 분석하세요.",
                    mike_security: "Database Activity Streaming으로 모든 DB 활동을 감시하세요.",
                    jenny_developer: "RDS Proxy와 Lambda로 연결 풀링까지 자동화해보세요!"
                }
            },
            'VPC': {
                1: {
                    base: "네트워크 보안과 서브넷 구성을 고려해보세요.",
                    alex_ceo: "네트워크 설계가 전체 아키텍처의 기반이에요!",
                    sarah_analyst: "트래픽 패턴을 분석해서 서브넷을 설계하세요.",
                    mike_security: "네트워크 레벨에서부터 보안을 강화해야 해요.",
                    jenny_developer: "Infrastructure as Code로 네트워크를 관리해보세요!"
                },
                2: {
                    base: "퍼블릭/프라이빗 서브넷과 NAT Gateway를 생각해보세요.",
                    alex_ceo: "NAT Gateway로 아웃바운드 트래픽을 안전하게 관리해요!",
                    sarah_analyst: "서브넷별 트래픽 분석으로 최적의 구성을 찾으세요.",
                    mike_security: "프라이빗 서브넷으로 내부 리소스를 완전히 격리하세요.",
                    jenny_developer: "Terraform으로 전체 네트워크 인프라를 코드화해보세요!"
                },
                3: {
                    base: "보안 그룹, NACL, VPC 엔드포인트를 포함한 완전한 네트워크 아키텍처를 설계해보세요.",
                    alex_ceo: "엔터프라이즈급 네트워크 보안으로 고객 신뢰를 확보해요!",
                    sarah_analyst: "VPC Flow Logs로 모든 네트워크 트래픽을 분석하세요.",
                    mike_security: "다층 보안으로 제로 트러스트 네트워크를 구축하세요.",
                    jenny_developer: "VPC 엔드포인트로 AWS 서비스 통신을 완전히 프라이빗하게 만들어보세요!"
                }
            }
        };
        
        // 기본 힌트 (카테고리가 없거나 매칭되지 않는 경우)
        const defaultHints = {
            1: {
                base: "AWS의 관리형 서비스를 활용해보세요.",
                alex_ceo: "관리형 서비스로 운영 비용을 대폭 절감할 수 있어요!",
                sarah_analyst: "관리형 서비스의 성능 지표를 분석해보세요.",
                mike_security: "AWS 관리형 서비스는 보안 패치가 자동으로 적용돼요.",
                jenny_developer: "관리형 서비스로 개발에만 집중할 수 있어요!"
            },
            2: {
                base: "고가용성과 비용 효율성을 동시에 고려해보세요.",
                alex_ceo: "고가용성으로 비즈니스 연속성을 보장하면서 비용도 최적화해요!",
                sarah_analyst: "가용성 지표와 비용 분석을 통해 최적점을 찾으세요.",
                mike_security: "고가용성 구성에서도 보안 요구사항을 만족해야 해요.",
                jenny_developer: "자동화로 고가용성과 비용 효율성을 동시에 달성해보세요!"
            },
            3: {
                base: "모니터링과 자동화를 포함한 완전한 솔루션을 설계해보세요.",
                alex_ceo: "완전 자동화로 운영팀 없이도 안정적인 서비스를 만들어요!",
                sarah_analyst: "종합적인 모니터링 대시보드로 모든 지표를 추적하세요.",
                mike_security: "자동화된 보안 모니터링과 대응 체계를 구축하세요.",
                jenny_developer: "GitOps와 CI/CD로 완전 자동화된 배포 파이프라인을 만들어보세요!"
            }
        };
        
        // 힌트 선택
        const categoryHints = enhancedHintTemplates[category] || defaultHints;
        const levelHints = categoryHints[hintLevel] || defaultHints[hintLevel];
        const npcSpecificHint = levelHints[this.currentNpc] || levelHints.base;
        
        return {
            hint: levelHints.base,
            message: npcSpecificHint,
            hintLevel: hintLevel,
            source: 'enhanced_fallback',
            npcId: this.currentNpc,
            category: category
        };
    }
    
    // Utility methods
    getRandomItem(array) {
        return array[Math.floor(Math.random() * array.length)];
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Public methods for GameManager integration
    async handleQuestionResult(result) {
        await this.showAnswerResponse(result.isCorrect, result);
    }
    
    async provideHint(questionData, hintLevel) {
        return await this.requestNpcHint(questionData, hintLevel);
    }
    
    getCurrentNpcData() {
        return this.currentNpc ? this.npcData[this.currentNpc] : null;
    }
    
    setTypingSpeed(speed) {
        this.typingSpeed = speed;
    }
    
    // Dialogue session management
    saveDialogueSession() {
        if (this.currentDialogueSession) {
            localStorage.setItem('npcDialogueSession', JSON.stringify(this.currentDialogueSession));
        }
    }
    
    loadDialogueSession() {
        const sessionData = localStorage.getItem('npcDialogueSession');
        if (sessionData) {
            this.currentDialogueSession = JSON.parse(sessionData);
        }
    }
    
    clearDialogueSession() {
        this.currentDialogueSession = null;
        localStorage.removeItem('npcDialogueSession');
    }
}

// Export for use in other modules
window.NPCSystem = NPCSystem;
