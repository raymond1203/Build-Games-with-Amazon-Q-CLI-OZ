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
            
            if (this.currentNpc) {
                await this.startNpcDialogue();
            } else {
                await this.loadQuestion();
            }
        } catch (error) {
            console.error('Error starting game session:', error);
            this.showNotification('게임 세션을 시작할 수 없습니다.', 'error');
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
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gameManager = new GameManager();
});
