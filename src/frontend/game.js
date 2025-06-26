/**
 * AWS Problem Solver Game - Main Game Logic
 */

class GameManager {
    constructor() {
        this.apiBaseUrl = this.getApiBaseUrl();
        this.currentUser = null;
        this.currentSession = null;
        this.currentQuestion = null;
        this.currentNpc = null;
        this.gameMode = null;
        this.questionTimer = null;
        this.timeRemaining = 0;
        this.hintsUsed = 0;
        this.questionsAnswered = 0;
        this.correctAnswers = 0;
        
        // Initialize NPC system
        this.npcSystem = null;
        
        this.init();
    }
    
    getApiBaseUrl() {
        // In production, this would be set via environment variables
        return window.location.hostname === 'localhost' 
            ? 'http://localhost:3000/dev'  // Local development
            : 'https://your-api-id.execute-api.region.amazonaws.com/dev';  // Production
    }
    
    init() {
        this.setupEventListeners();
        this.loadUserData();
        this.showLoadingScreen();
        
        // Initialize NPC system
        this.npcSystem = new NPCSystem(this);
        
        // Simulate loading time
        setTimeout(() => {
            this.hideLoadingScreen();
            this.showWelcomeScreen();
        }, 2000);
    }
    
    setupEventListeners() {
        // Welcome screen
        document.getElementById('start-game-btn').addEventListener('click', () => this.startGame());
        document.querySelectorAll('.mode-card').forEach(card => {
            card.addEventListener('click', () => this.selectGameMode(card.dataset.mode));
        });
        
        // NPC selection
        document.querySelectorAll('.npc-card').forEach(card => {
            card.addEventListener('click', () => this.selectNpc(card.dataset.npc));
        });
        document.getElementById('back-to-welcome-btn').addEventListener('click', () => this.showWelcomeScreen());
        
        // Game screen
        document.getElementById('submit-answer-btn').addEventListener('click', () => this.submitAnswer());
        document.getElementById('hint-btn').addEventListener('click', () => this.requestHint());
        document.getElementById('continue-dialogue-btn').addEventListener('click', () => this.continueDialogue());
        document.getElementById('skip-dialogue-btn').addEventListener('click', () => this.skipDialogue());
        
        // Result screen
        document.getElementById('next-question-btn').addEventListener('click', () => this.loadNextQuestion());
        document.getElementById('review-answer-btn').addEventListener('click', () => this.reviewAnswer());
        document.getElementById('end-session-btn').addEventListener('click', () => this.endSession());
        
        // Modals
        document.getElementById('hint-modal-close').addEventListener('click', () => this.closeHintModal());
        document.getElementById('use-hint-btn').addEventListener('click', () => this.useHint());
        document.getElementById('cancel-hint-btn').addEventListener('click', () => this.closeHintModal());
        
        // Settings
        document.getElementById('settings-btn').addEventListener('click', () => this.showSettings());
        document.getElementById('settings-modal-close').addEventListener('click', () => this.closeSettings());
        document.getElementById('save-settings-btn').addEventListener('click', () => this.saveSettings());
        document.getElementById('cancel-settings-btn').addEventListener('click', () => this.closeSettings());
        
        // Leaderboard
        document.getElementById('back-to-game-btn').addEventListener('click', () => this.showGameScreen());
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchLeaderboardTab(btn.dataset.type));
        });
    }
    
    // Screen Management
    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(screenId).classList.add('active');
    }
    
    showLoadingScreen() {
        document.getElementById('loading-screen').classList.remove('hidden');
        document.getElementById('game-container').classList.add('hidden');
    }
    
    hideLoadingScreen() {
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('game-container').classList.remove('hidden');
    }
    
    showWelcomeScreen() {
        this.showScreen('welcome-screen');
        this.resetGameState();
    }
    
    showNpcSelectionScreen() {
        this.showScreen('npc-selection-screen');
    }
    
    showGameScreen() {
        this.showScreen('game-screen');
    }
    
    showResultScreen() {
        this.showScreen('result-screen');
    }
    
    showLeaderboardScreen() {
        this.showScreen('leaderboard-screen');
        this.loadLeaderboard();
    }
    
    // Game Flow
    selectGameMode(mode) {
        // Remove previous selections
        document.querySelectorAll('.mode-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select current mode
        document.querySelector(`[data-mode="${mode}"]`).classList.add('selected');
        this.gameMode = mode;
    }
    
    startGame() {
        const username = document.getElementById('username-input').value.trim();
        
        if (!username) {
            this.showNotification('사용자 이름을 입력해주세요.', 'warning');
            return;
        }
        
        if (!this.gameMode) {
            this.showNotification('게임 모드를 선택해주세요.', 'warning');
            return;
        }
        
        this.currentUser = {
            id: this.generateUserId(),
            username: username,
            score: 0,
            level: 1,
            accuracy: 0
        };
        
        this.saveUserData();
        this.updateUserStats();
        
        if (this.gameMode === 'npc') {
            this.showNpcSelectionScreen();
        } else {
            this.startGameSession();
        }
    }
    
    selectNpc(npcId) {
        // Remove previous selections
        document.querySelectorAll('.npc-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select current NPC
        document.querySelector(`[data-npc="${npcId}"]`).classList.add('selected');
        this.currentNpc = npcId;
        
        // Start game after short delay
        setTimeout(() => {
            this.startGameSession();
        }, 500);
    }
    
    async startGameSession() {
        try {
            this.showGameScreen();
            this.initializeSession();
            
            if (this.currentNpc && this.npcSystem) {
                await this.npcSystem.startNpcDialogue(this.currentNpc);
            } else {
                await this.loadQuestion();
            }
        } catch (error) {
            console.error('Error starting game session:', error);
            this.showNotification('게임 세션을 시작할 수 없습니다.', 'error');
        }
    }
        }
    }
    
    initializeSession() {
        this.currentSession = {
            id: this.generateSessionId(),
            startTime: new Date(),
            questionsAnswered: 0,
            correctAnswers: 0,
            totalScore: 0,
            hintsUsed: 0
        };
        
        this.questionsAnswered = 0;
        this.correctAnswers = 0;
        this.updateProgress();
    }
    
    async loadQuestion() {
        try {
            this.showLoadingIndicator();
            
            let endpoint;
            let params = new URLSearchParams();
            
            switch (this.gameMode) {
                case 'random':
                    endpoint = '/questions/random';
                    break;
                case 'adaptive':
                    endpoint = '/questions/adaptive';
                    params.append('userId', this.currentUser.id);
                    break;
                case 'npc':
                    endpoint = '/questions/npc';
                    params.append('npcId', this.currentNpc);
                    params.append('userLevel', this.currentUser.level);
                    break;
            }
            
            const url = `${this.apiBaseUrl}${endpoint}?${params}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (this.gameMode === 'npc' && data.questions && data.questions.length > 0) {
                this.currentQuestion = data.questions[0];
            } else {
                this.currentQuestion = data.question;
            }
            
            this.displayQuestion();
            this.startQuestionTimer();
            
        } catch (error) {
            console.error('Error loading question:', error);
            this.showNotification('문제를 불러올 수 없습니다.', 'error');
        } finally {
            this.hideLoadingIndicator();
        }
    }
    
    displayQuestion() {
        if (!this.currentQuestion) return;
        
        // Update question metadata
        document.getElementById('question-category').textContent = this.currentQuestion.category;
        document.getElementById('question-difficulty').textContent = this.currentQuestion.difficulty;
        document.getElementById('question-points').textContent = `${this.currentQuestion.points} pts`;
        
        // Update scenario
        document.getElementById('scenario-title').textContent = this.currentQuestion.scenario.title;
        document.getElementById('scenario-description').textContent = this.currentQuestion.scenario.description;
        document.getElementById('scenario-context').textContent = this.currentQuestion.scenario.context || '';
        
        // Update question text
        document.getElementById('question-text').textContent = this.currentQuestion.question;
        
        // Generate options
        this.generateOptions();
        
        // Reset UI state
        this.hintsUsed = 0;
        document.getElementById('hint-count').textContent = '3';
        document.getElementById('submit-answer-btn').disabled = true;
    }
    
    generateOptions() {
        const container = document.getElementById('options-container');
        container.innerHTML = '';
        
        this.currentQuestion.options.forEach(option => {
            const optionElement = document.createElement('div');
            optionElement.className = 'option-item';
            optionElement.dataset.optionId = option.id;
            
            optionElement.innerHTML = `
                <div class="option-letter">${option.id}</div>
                <div class="option-text">${option.text}</div>
            `;
            
            optionElement.addEventListener('click', () => this.selectOption(option.id));
            container.appendChild(optionElement);
        });
    }
    
    selectOption(optionId) {
        // Remove previous selections
        document.querySelectorAll('.option-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Select current option
        document.querySelector(`[data-option-id="${optionId}"]`).classList.add('selected');
        
        // Enable submit button
        document.getElementById('submit-answer-btn').disabled = false;
        
        this.selectedAnswer = optionId;
    }
    
    async submitAnswer() {
        if (!this.selectedAnswer) return;
        
        try {
            this.stopQuestionTimer();
            this.showLoadingIndicator();
            
            const requestData = {
                action: 'validate_answer',
                questionId: this.currentQuestion.questionId,
                selectedAnswer: this.selectedAnswer,
                userId: this.currentUser.id,
                timeSpent: this.currentQuestion.estimatedTime - this.timeRemaining,
                hintsUsed: this.hintsUsed
            };
            
            const response = await fetch(`${this.apiBaseUrl}/answer`, {
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
            this.processAnswerResult(result);
            
        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showNotification('답안을 제출할 수 없습니다.', 'error');
        } finally {
            this.hideLoadingIndicator();
        }
    }
    
    processAnswerResult(result) {
        this.questionsAnswered++;
        if (result.isCorrect) {
            this.correctAnswers++;
        }
        
        // Update user stats
        this.currentUser.score += result.score.points;
        this.currentUser.accuracy = Math.round((this.correctAnswers / this.questionsAnswered) * 100);
        
        this.updateUserStats();
        this.updateProgress();
        this.displayResult(result);
        this.showResultScreen();
    }
    
    displayResult(result) {
        const resultIcon = document.getElementById('result-icon');
        const resultTitle = document.getElementById('result-title');
        const resultMessage = document.getElementById('result-message');
        
        if (result.isCorrect) {
            resultIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
            resultIcon.className = 'result-icon correct';
            resultTitle.textContent = '정답입니다!';
            resultMessage.textContent = this.getCorrectAnswerMessage();
        } else {
            resultIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
            resultIcon.className = 'result-icon incorrect';
            resultTitle.textContent = '틀렸습니다.';
            resultMessage.textContent = `정답은 ${result.correctAnswer}번이었습니다.`;
        }
        
        // Update score breakdown
        document.getElementById('base-score').textContent = result.score.breakdown.base;
        document.getElementById('difficulty-bonus').textContent = `+${result.score.breakdown.difficulty}`;
        document.getElementById('time-bonus').textContent = `+${result.score.breakdown.time}`;
        document.getElementById('hint-penalty').textContent = result.score.breakdown.hint_penalty;
        document.getElementById('total-score').textContent = result.score.points;
        
        // Update explanation
        document.getElementById('explanation-text').textContent = result.explanation;
        
        // Update learning resources
        this.displayLearningResources(result.learning_resources || []);
    }
    
    displayLearningResources(resources) {
        const container = document.getElementById('learning-resources');
        
        if (resources.length === 0) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'block';
        const resourcesList = container.querySelector('.resources-list') || document.createElement('div');
        resourcesList.className = 'resources-list';
        resourcesList.innerHTML = '';
        
        resources.forEach(resource => {
            const resourceElement = document.createElement('a');
            resourceElement.href = resource.url;
            resourceElement.target = '_blank';
            resourceElement.className = 'resource-link';
            resourceElement.innerHTML = `
                <i class="fas fa-external-link-alt"></i>
                ${resource.title}
            `;
            resourcesList.appendChild(resourceElement);
        });
        
        if (!container.querySelector('.resources-list')) {
            container.appendChild(resourcesList);
        }
    }
    
    // Timer Management
    startQuestionTimer() {
        this.timeRemaining = this.currentQuestion.estimatedTime || 60;
        this.updateTimerDisplay();
        
        this.questionTimer = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            if (this.timeRemaining <= 0) {
                this.handleTimeUp();
            }
        }, 1000);
    }
    
    stopQuestionTimer() {
        if (this.questionTimer) {
            clearInterval(this.questionTimer);
            this.questionTimer = null;
        }
    }
    
    updateTimerDisplay() {
        const timerElement = document.getElementById('question-timer');
        timerElement.textContent = `${this.timeRemaining}s`;
        
        if (this.timeRemaining <= 10) {
            timerElement.style.color = '#ff4444';
        } else if (this.timeRemaining <= 30) {
            timerElement.style.color = '#ff9900';
        } else {
            timerElement.style.color = '#333';
        }
    }
    
    handleTimeUp() {
        this.stopQuestionTimer();
        this.showNotification('시간이 초과되었습니다!', 'warning');
        
        if (!this.selectedAnswer) {
            // Auto-submit with no answer
            this.selectedAnswer = 'A'; // Default to first option
            this.submitAnswer();
        }
    }
    
    // Utility Functions
    generateUserId() {
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    updateUserStats() {
        if (!this.currentUser) return;
        
        document.getElementById('user-score').textContent = this.currentUser.score;
        document.getElementById('user-level').textContent = this.currentUser.level;
        document.getElementById('user-accuracy').textContent = `${this.currentUser.accuracy}%`;
    }
    
    updateProgress() {
        const maxQuestions = 10; // Default session length
        const progress = (this.questionsAnswered / maxQuestions) * 100;
        
        document.getElementById('progress-fill').style.width = `${progress}%`;
        document.getElementById('progress-text').textContent = `${this.questionsAnswered}/${maxQuestions}`;
    }
    
    resetGameState() {
        this.currentSession = null;
        this.currentQuestion = null;
        this.currentNpc = null;
        this.gameMode = null;
        this.selectedAnswer = null;
        this.questionsAnswered = 0;
        this.correctAnswers = 0;
        this.hintsUsed = 0;
        
        this.stopQuestionTimer();
        
        // Reset UI
        document.querySelectorAll('.mode-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.querySelectorAll('.npc-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        this.updateProgress();
    }
    
    getCorrectAnswerMessage() {
        const messages = [
            '훌륭한 선택입니다!',
            '완벽합니다!',
            '정확한 답변이네요!',
            '잘하셨습니다!',
            '멋진 해결책입니다!'
        ];
        return messages[Math.floor(Math.random() * messages.length)];
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show with animation
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
    
    showLoadingIndicator() {
        // Implementation for loading indicator
    }
    
    hideLoadingIndicator() {
        // Implementation for loading indicator
    }
    
    // NPC Integration Methods
    async requestHint() {
        if (!this.currentQuestion) {
            this.showNotification('문제가 로드되지 않았습니다.', 'warning');
            return;
        }
        
        if (this.hintsUsed >= 3) {
            this.showNotification('더 이상 힌트를 사용할 수 없습니다.', 'warning');
            return;
        }
        
        try {
            if (this.npcSystem && this.currentNpc) {
                const hintData = await this.npcSystem.provideHint(this.currentQuestion, this.hintsUsed + 1);
                this.hintsUsed++;
                this.updateHintButton();
            } else {
                // Fallback to basic hint system
                this.showBasicHint();
            }
        } catch (error) {
            console.error('Error requesting hint:', error);
            this.showNotification('힌트를 가져올 수 없습니다.', 'error');
        }
    }
    
    showBasicHint() {
        const hints = [
            "AWS의 관리형 서비스를 고려해보세요.",
            "비용 효율성과 확장성을 동시에 고려해야 합니다.",
            "고가용성을 위한 다중 AZ 구성을 생각해보세요."
        ];
        
        const hint = hints[Math.min(this.hintsUsed, hints.length - 1)];
        this.showNotification(hint, 'info');
        this.hintsUsed++;
        this.updateHintButton();
    }
    
    updateHintButton() {
        const hintBtn = document.getElementById('hint-btn');
        const remainingHints = 3 - this.hintsUsed;
        
        if (remainingHints <= 0) {
            hintBtn.disabled = true;
            hintBtn.textContent = '힌트 없음';
        } else {
            hintBtn.textContent = `힌트 (${remainingHints}개 남음)`;
        }
    }
    
    async handleAnswerResult(result) {
        if (this.npcSystem && this.currentNpc) {
            await this.npcSystem.handleQuestionResult(result);
        }
        
        // Update game statistics
        this.questionsAnswered++;
        if (result.isCorrect) {
            this.correctAnswers++;
        }
        
        this.updateGameStats();
    }
    
    updateGameStats() {
        const accuracy = this.questionsAnswered > 0 ? 
            Math.round((this.correctAnswers / this.questionsAnswered) * 100) : 0;
        
        document.getElementById('questions-answered').textContent = this.questionsAnswered;
        document.getElementById('correct-answers').textContent = this.correctAnswers;
        document.getElementById('accuracy-rate').textContent = `${accuracy}%`;
    }
    
    // Question Management Methods
    async loadQuestion() {
        try {
            this.showLoadingIndicator();
            
            // Mock question data for now - will be replaced with API call
            const mockQuestion = this.generateMockQuestion();
            
            this.currentQuestion = mockQuestion;
            this.displayQuestion(mockQuestion);
            this.startQuestionTimer();
            
            this.hideLoadingIndicator();
            
        } catch (error) {
            console.error('Error loading question:', error);
            this.showNotification('문제를 불러올 수 없습니다.', 'error');
            this.hideLoadingIndicator();
        }
    }
    
    generateMockQuestion() {
        const questions = [
            {
                questionId: 'q001',
                category: 'EC2',
                difficulty: 'medium',
                points: 100,
                timeLimit: 60,
                scenario: {
                    title: '웹 애플리케이션 확장성 문제',
                    description: '스타트업 TechStart의 웹 애플리케이션이 갑작스러운 트래픽 증가로 인해 응답 시간이 느려지고 있습니다.',
                    context: '현재 단일 EC2 인스턴스에서 실행 중이며, 피크 시간대에 CPU 사용률이 90%를 넘나들고 있습니다.'
                },
                question: '이 상황에서 가장 적절한 AWS 솔루션은 무엇입니까?',
                options: [
                    {
                        id: 'A',
                        text: 'EC2 인스턴스의 크기를 더 큰 인스턴스 타입으로 업그레이드한다.'
                    },
                    {
                        id: 'B',
                        text: 'Application Load Balancer와 Auto Scaling Group을 구성하여 여러 인스턴스에 트래픽을 분산한다.'
                    },
                    {
                        id: 'C',
                        text: 'CloudFront CDN만 추가하여 정적 콘텐츠를 캐싱한다.'
                    },
                    {
                        id: 'D',
                        text: 'RDS 데이터베이스를 더 큰 인스턴스로 업그레이드한다.'
                    }
                ],
                correctAnswer: 'B',
                explanation: 'Auto Scaling Group과 Load Balancer를 사용하면 트래픽 증가에 따라 자동으로 인스턴스를 추가/제거하여 비용 효율적으로 확장성을 확보할 수 있습니다. 단순히 인스턴스 크기를 늘리는 것(수직 확장)보다 수평 확장이 더 효과적이고 경제적입니다.'
            },
            {
                questionId: 'q002',
                category: 'S3',
                difficulty: 'easy',
                points: 75,
                timeLimit: 45,
                scenario: {
                    title: '데이터 백업 및 보관',
                    description: '회사에서 중요한 문서들을 안전하게 백업하고 장기간 보관해야 합니다.',
                    context: '매월 약 100GB의 데이터가 생성되며, 자주 접근하지 않지만 필요시 빠르게 복구할 수 있어야 합니다.'
                },
                question: '비용 효율적인 장기 보관을 위한 가장 적절한 S3 스토리지 클래스는?',
                options: [
                    {
                        id: 'A',
                        text: 'S3 Standard - 일반적인 용도로 자주 액세스되는 데이터용'
                    },
                    {
                        id: 'B',
                        text: 'S3 Standard-IA (Infrequent Access) - 자주 액세스하지 않지만 빠른 액세스가 필요한 데이터용'
                    },
                    {
                        id: 'C',
                        text: 'S3 Glacier - 아카이브 및 장기 백업용'
                    },
                    {
                        id: 'D',
                        text: 'S3 One Zone-IA - 단일 가용 영역에 저장되는 저빈도 액세스 데이터용'
                    }
                ],
                correctAnswer: 'B',
                explanation: 'S3 Standard-IA는 자주 액세스하지 않지만 필요시 즉시 사용할 수 있어야 하는 데이터에 적합합니다. Standard보다 저렴하면서도 밀리초 단위의 빠른 액세스가 가능합니다.'
            }
        ];
        
        return questions[Math.floor(Math.random() * questions.length)];
    }
    
    displayQuestion(question) {
        // Update question metadata
        document.getElementById('question-category').textContent = question.category;
        document.getElementById('question-difficulty').textContent = question.difficulty;
        document.getElementById('question-difficulty').className = `question-difficulty ${question.difficulty}`;
        document.getElementById('question-points').textContent = `${question.points} pts`;
        
        // Update scenario
        document.getElementById('scenario-title').textContent = question.scenario.title;
        document.getElementById('scenario-description').textContent = question.scenario.description;
        document.getElementById('scenario-context').textContent = question.scenario.context;
        
        // Update question text
        document.getElementById('question-text').textContent = question.question;
        
        // Generate options
        this.generateOptions(question.options);
        
        // Reset UI state
        this.resetQuestionUI();
    }
    
    generateOptions(options) {
        const container = document.getElementById('options-container');
        container.innerHTML = '';
        
        options.forEach(option => {
            const optionElement = document.createElement('div');
            optionElement.className = 'option-item';
            optionElement.dataset.optionId = option.id;
            
            optionElement.innerHTML = `
                <div class="option-letter">${option.id}</div>
                <div class="option-text">${option.text}</div>
                <div class="answer-feedback"></div>
            `;
            
            optionElement.addEventListener('click', () => this.selectOption(option.id));
            container.appendChild(optionElement);
        });
    }
    
    selectOption(optionId) {
        // Remove previous selections
        document.querySelectorAll('.option-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Select current option
        const selectedOption = document.querySelector(`[data-option-id="${optionId}"]`);
        selectedOption.classList.add('selected');
        
        // Enable submit button
        document.getElementById('submit-answer-btn').disabled = false;
        
        // Store selected answer
        this.selectedAnswer = optionId;
    }
    
    async submitAnswer() {
        if (!this.selectedAnswer || !this.currentQuestion) {
            this.showNotification('답안을 선택해주세요.', 'warning');
            return;
        }
        
        // Stop timer
        this.stopQuestionTimer();
        
        // Disable all options
        document.querySelectorAll('.option-item').forEach(item => {
            item.classList.add('disabled');
        });
        
        // Disable submit button
        document.getElementById('submit-answer-btn').disabled = true;
        
        // Show correct/incorrect answers with animation
        await this.revealAnswers();
        
        // Calculate score
        const result = this.calculateScore();
        
        // Handle NPC response
        if (this.npcSystem && this.currentNpc) {
            await this.handleAnswerResult(result);
        }
        
        // Show result after delay
        setTimeout(() => {
            this.showResultScreen();
            this.displayResult(result);
        }, 2000);
    }
    
    async revealAnswers() {
        const correctAnswer = this.currentQuestion.correctAnswer;
        const selectedAnswer = this.selectedAnswer;
        
        // Reveal correct answer
        const correctOption = document.querySelector(`[data-option-id="${correctAnswer}"]`);
        correctOption.classList.add('correct', 'reveal-correct');
        
        // Reveal incorrect answer if different from correct
        if (selectedAnswer !== correctAnswer) {
            const incorrectOption = document.querySelector(`[data-option-id="${selectedAnswer}"]`);
            incorrectOption.classList.add('incorrect', 'reveal-incorrect');
        }
        
        // Wait for animation
        await this.sleep(600);
    }
    
    calculateScore() {
        const isCorrect = this.selectedAnswer === this.currentQuestion.correctAnswer;
        const baseScore = this.currentQuestion.points;
        const timeBonus = Math.max(0, Math.floor((this.timeRemaining / this.currentQuestion.timeLimit) * 50));
        const hintPenalty = this.hintsUsed * 10;
        
        let difficultyMultiplier = 1;
        switch (this.currentQuestion.difficulty) {
            case 'easy': difficultyMultiplier = 1; break;
            case 'medium': difficultyMultiplier = 1.5; break;
            case 'hard': difficultyMultiplier = 2; break;
        }
        
        const totalScore = isCorrect ? 
            Math.floor((baseScore * difficultyMultiplier) + timeBonus - hintPenalty) : 0;
        
        return {
            isCorrect,
            selectedAnswer: this.selectedAnswer,
            correctAnswer: this.currentQuestion.correctAnswer,
            baseScore,
            difficultyMultiplier,
            timeBonus,
            hintPenalty,
            totalScore,
            explanation: this.currentQuestion.explanation
        };
    }
    
    displayResult(result) {
        // Update result header
        const resultIcon = document.getElementById('result-icon');
        const resultTitle = document.getElementById('result-title');
        const resultMessage = document.getElementById('result-message');
        
        if (result.isCorrect) {
            resultIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
            resultIcon.className = 'result-icon correct';
            resultTitle.textContent = '정답입니다!';
            resultMessage.textContent = this.getRandomSuccessMessage();
        } else {
            resultIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
            resultIcon.className = 'result-icon incorrect';
            resultTitle.textContent = '틀렸습니다';
            resultMessage.textContent = `정답은 ${result.correctAnswer}번이었습니다.`;
        }
        
        // Update score breakdown
        document.getElementById('base-score').textContent = result.baseScore;
        document.getElementById('difficulty-bonus').textContent = `+${Math.floor(result.baseScore * (result.difficultyMultiplier - 1))}`;
        document.getElementById('time-bonus').textContent = `+${result.timeBonus}`;
        document.getElementById('hint-penalty').textContent = `-${result.hintPenalty}`;
        document.getElementById('total-score').textContent = result.totalScore;
        
        // Update explanation
        document.getElementById('explanation-text').textContent = result.explanation;
    }
    
    resetQuestionUI() {
        this.selectedAnswer = null;
        this.hintsUsed = 0;
        this.updateHintButton();
        document.getElementById('submit-answer-btn').disabled = true;
        
        // Reset option states
        document.querySelectorAll('.option-item').forEach(item => {
            item.classList.remove('selected', 'correct', 'incorrect', 'disabled', 'reveal-correct', 'reveal-incorrect');
        });
    }
    
    // Timer Management
    startQuestionTimer() {
        if (this.questionTimer) {
            clearInterval(this.questionTimer);
        }
        
        this.timeRemaining = this.currentQuestion.timeLimit;
        this.updateTimerDisplay();
        
        this.questionTimer = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            if (this.timeRemaining <= 10) {
                document.querySelector('.question-timer').classList.add('warning');
            }
            
            if (this.timeRemaining <= 0) {
                this.timeUp();
            }
        }, 1000);
    }
    
    stopQuestionTimer() {
        if (this.questionTimer) {
            clearInterval(this.questionTimer);
            this.questionTimer = null;
        }
    }
    
    updateTimerDisplay() {
        document.getElementById('question-timer').textContent = `${this.timeRemaining}s`;
    }
    
    timeUp() {
        this.stopQuestionTimer();
        this.showNotification('시간이 초과되었습니다!', 'warning');
        
        // Auto-submit if no answer selected
        if (!this.selectedAnswer) {
            this.selectedAnswer = 'A'; // Default to first option
        }
        
        this.submitAnswer();
    }
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gameManager = new GameManager();
});
    
    // Data Persistence
    saveUserData() {
        if (this.currentUser) {
            localStorage.setItem('awsGameUser', JSON.stringify(this.currentUser));
        }
    }
    
    loadUserData() {
        const userData = localStorage.getItem('awsGameUser');
        if (userData) {
            this.currentUser = JSON.parse(userData);
            this.updateUserStats();
        }
    }
    
    // Additional Game Flow Methods
    async loadNextQuestion() {
        this.resetGameState();
        await this.loadQuestion();
        this.showGameScreen();
    }
    
    reviewAnswer() {
        // Show detailed explanation or analysis
        this.showNotification('답안 분석 기능은 곧 추가될 예정입니다.', 'info');
    }
    
    endSession() {
        this.resetGameState();
        this.showWelcomeScreen();
        this.showNotification('게임 세션이 종료되었습니다.', 'info');
    }
    
    resetGameState() {
        this.currentQuestion = null;
        this.selectedAnswer = null;
        this.hintsUsed = 0;
        this.timeRemaining = 0;
        this.stopQuestionTimer();
        
        // Reset UI elements
        document.querySelector('.question-timer').classList.remove('warning');
    }
    
    initializeSession() {
        this.currentSession = {
            id: this.generateSessionId(),
            startTime: new Date(),
            questionsAnswered: 0,
            correctAnswers: 0,
            totalScore: 0,
            npcId: this.currentNpc,
            gameMode: this.gameMode
        };
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    generateUserId() {
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    updateUserStats() {
        if (this.currentUser) {
            // Update UI with user stats if elements exist
            const scoreElement = document.getElementById('user-score');
            if (scoreElement) {
                scoreElement.textContent = this.currentUser.totalScore || 0;
            }
        }
    }
    
    // Modal Management
    closeHintModal() {
        // Implementation for hint modal
        this.showNotification('힌트 모달 기능은 곧 추가될 예정입니다.', 'info');
    }
    
    useHint() {
        this.requestHint();
        this.closeHintModal();
    }
    
    showSettings() {
        this.showNotification('설정 기능은 곧 추가될 예정입니다.', 'info');
    }
    
    closeSettings() {
        // Implementation for settings modal
    }
    
    saveSettings() {
        this.showNotification('설정이 저장되었습니다.', 'success');
        this.closeSettings();
    }
    
    // Leaderboard
    loadLeaderboard() {
        this.showNotification('리더보드 기능은 곧 추가될 예정입니다.', 'info');
    }
    
    switchLeaderboardTab(type) {
        // Implementation for leaderboard tabs
        console.log('Switching to leaderboard tab:', type);
    }
