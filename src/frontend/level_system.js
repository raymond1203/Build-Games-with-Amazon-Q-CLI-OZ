/**
 * AWS Problem Solver Game - Level and Achievement System
 * 레벨 시스템 및 성취 배지 관리
 */

class LevelSystem {
    constructor(gameManager) {
        this.gameManager = gameManager;
        this.currentLevel = 1;
        this.currentExp = 0;
        this.totalScore = 0;
        this.achievements = [];
        this.streakCount = 0;
        this.maxStreak = 0;
        
        // 레벨별 필요 경험치 (누적)
        this.levelThresholds = [
            0,      // Level 1
            100,    // Level 2
            300,    // Level 3
            600,    // Level 4
            1000,   // Level 5
            1500,   // Level 6
            2100,   // Level 7
            2800,   // Level 8
            3600,   // Level 9
            4500,   // Level 10
            5500,   // Level 11
            6600,   // Level 12
            7800,   // Level 13
            9100,   // Level 14
            10500,  // Level 15
            12000,  // Level 16
            13600,  // Level 17
            15300,  // Level 18
            17100,  // Level 19
            19000   // Level 20 (최대)
        ];
        
        // AWS 전문가 등급
        this.expertTitles = {
            1: { title: "AWS 입문자", color: "#95a5a6", icon: "🌱" },
            3: { title: "클라우드 탐험가", color: "#3498db", icon: "🔍" },
            5: { title: "AWS 실무자", color: "#2ecc71", icon: "⚡" },
            8: { title: "솔루션 아키텍트", color: "#f39c12", icon: "🏗️" },
            12: { title: "클라우드 전문가", color: "#e74c3c", icon: "🎯" },
            15: { title: "AWS 마스터", color: "#9b59b6", icon: "👑" },
            18: { title: "클라우드 구루", color: "#1abc9c", icon: "🧙‍♂️" },
            20: { title: "AWS 레전드", color: "#f1c40f", icon: "⭐" }
        };
        
        // 성취 배지 정의
        this.achievementDefinitions = {
            first_correct: {
                id: 'first_correct',
                name: '첫 번째 정답',
                description: '첫 번째 문제를 맞혔습니다!',
                icon: '🎯',
                color: '#2ecc71',
                condition: (stats) => stats.correctAnswers >= 1
            },
            streak_5: {
                id: 'streak_5',
                name: '연속 정답 5개',
                description: '5문제를 연속으로 맞혔습니다!',
                icon: '🔥',
                color: '#e74c3c',
                condition: (stats) => stats.maxStreak >= 5
            },
            streak_10: {
                id: 'streak_10',
                name: '연속 정답 10개',
                description: '10문제를 연속으로 맞혔습니다!',
                icon: '💥',
                color: '#f39c12',
                condition: (stats) => stats.maxStreak >= 10
            },
            perfect_score: {
                id: 'perfect_score',
                name: '완벽한 점수',
                description: '힌트 없이 시간 내에 정답을 맞혔습니다!',
                icon: '💎',
                color: '#9b59b6',
                condition: (stats, lastResult) => lastResult && lastResult.isCorrect && lastResult.hintPenalty === 0 && lastResult.timeBonus > 0
            },
            speed_demon: {
                id: 'speed_demon',
                name: '스피드 데몬',
                description: '10초 이내에 정답을 맞혔습니다!',
                icon: '⚡',
                color: '#f1c40f',
                condition: (stats, lastResult) => lastResult && lastResult.isCorrect && lastResult.timeBonus >= 40
            },
            ec2_expert: {
                id: 'ec2_expert',
                name: 'EC2 전문가',
                description: 'EC2 관련 문제 10개를 맞혔습니다!',
                icon: '🖥️',
                color: '#3498db',
                condition: (stats) => stats.categoryStats && stats.categoryStats.EC2 >= 10
            },
            s3_master: {
                id: 's3_master',
                name: 'S3 마스터',
                description: 'S3 관련 문제 10개를 맞혔습니다!',
                icon: '🗄️',
                color: '#27ae60',
                condition: (stats) => stats.categoryStats && stats.categoryStats.S3 >= 10
            },
            lambda_guru: {
                id: 'lambda_guru',
                name: 'Lambda 구루',
                description: 'Lambda 관련 문제 10개를 맞혔습니다!',
                icon: '⚡',
                color: '#e67e22',
                condition: (stats) => stats.categoryStats && stats.categoryStats.Lambda >= 10
            },
            accuracy_master: {
                id: 'accuracy_master',
                name: '정확도 마스터',
                description: '정답률 90% 이상을 달성했습니다!',
                icon: '🎯',
                color: '#8e44ad',
                condition: (stats) => stats.questionsAnswered >= 10 && (stats.correctAnswers / stats.questionsAnswered) >= 0.9
            },
            persistent_learner: {
                id: 'persistent_learner',
                name: '끈기있는 학습자',
                description: '50문제를 풀었습니다!',
                icon: '📚',
                color: '#34495e',
                condition: (stats) => stats.questionsAnswered >= 50
            },
            high_scorer: {
                id: 'high_scorer',
                name: '고득점자',
                description: '총 점수 5000점을 달성했습니다!',
                icon: '🏆',
                color: '#f39c12',
                condition: (stats) => stats.totalScore >= 5000
            }
        };
        
        this.init();
    }
    
    init() {
        this.loadUserProgress();
        this.updateUI();
    }
    
    // 점수 추가 및 레벨 계산
    addScore(score, questionResult = null) {
        this.totalScore += score;
        this.currentExp += score;
        
        // 연속 정답 처리
        if (questionResult && questionResult.isCorrect) {
            this.streakCount++;
            this.maxStreak = Math.max(this.maxStreak, this.streakCount);
        } else {
            this.streakCount = 0;
        }
        
        // 레벨업 확인
        const newLevel = this.calculateLevel();
        const leveledUp = newLevel > this.currentLevel;
        
        if (leveledUp) {
            this.currentLevel = newLevel;
            this.showLevelUpAnimation();
        }
        
        // 성취 배지 확인
        this.checkAchievements(questionResult);
        
        // UI 업데이트
        this.updateUI();
        
        // 데이터 저장
        this.saveUserProgress();
        
        return {
            leveledUp,
            newLevel: this.currentLevel,
            newAchievements: this.getRecentAchievements()
        };
    }
    
    calculateLevel() {
        for (let i = this.levelThresholds.length - 1; i >= 0; i--) {
            if (this.currentExp >= this.levelThresholds[i]) {
                return i + 1;
            }
        }
        return 1;
    }
    
    getExpForNextLevel() {
        if (this.currentLevel >= this.levelThresholds.length) {
            return this.levelThresholds[this.levelThresholds.length - 1];
        }
        return this.levelThresholds[this.currentLevel];
    }
    
    getExpProgress() {
        const currentLevelExp = this.currentLevel > 1 ? this.levelThresholds[this.currentLevel - 2] : 0;
        const nextLevelExp = this.getExpForNextLevel();
        const progressExp = this.currentExp - currentLevelExp;
        const requiredExp = nextLevelExp - currentLevelExp;
        
        return {
            current: progressExp,
            required: requiredExp,
            percentage: Math.min((progressExp / requiredExp) * 100, 100)
        };
    }
    
    getCurrentTitle() {
        let title = this.expertTitles[1]; // 기본값
        
        for (const level in this.expertTitles) {
            if (this.currentLevel >= parseInt(level)) {
                title = this.expertTitles[level];
            }
        }
        
        return title;
    }
    
    checkAchievements(questionResult = null) {
        const stats = this.getPlayerStats();
        const newAchievements = [];
        
        for (const achievementId in this.achievementDefinitions) {
            const achievement = this.achievementDefinitions[achievementId];
            
            // 이미 획득한 배지는 건너뛰기
            if (this.achievements.includes(achievementId)) {
                continue;
            }
            
            // 조건 확인
            if (achievement.condition(stats, questionResult)) {
                this.achievements.push(achievementId);
                newAchievements.push(achievement);
                this.showAchievementNotification(achievement);
            }
        }
        
        return newAchievements;
    }
    
    getPlayerStats() {
        const gameManager = this.gameManager;
        return {
            correctAnswers: gameManager.correctAnswers || 0,
            questionsAnswered: gameManager.questionsAnswered || 0,
            totalScore: this.totalScore,
            maxStreak: this.maxStreak,
            currentStreak: this.streakCount,
            categoryStats: this.getCategoryStats()
        };
    }
    
    getCategoryStats() {
        // 카테고리별 통계는 추후 구현
        return {
            EC2: 0,
            S3: 0,
            Lambda: 0,
            RDS: 0,
            VPC: 0
        };
    }
    
    showLevelUpAnimation() {
        const title = this.getCurrentTitle();
        
        // 레벨업 모달 생성
        const modal = document.createElement('div');
        modal.className = 'level-up-modal';
        modal.innerHTML = `
            <div class="level-up-content">
                <div class="level-up-animation">
                    <div class="level-up-icon">${title.icon}</div>
                    <h2>레벨 업!</h2>
                    <div class="level-display">
                        <span class="level-number">${this.currentLevel}</span>
                    </div>
                    <div class="title-display" style="color: ${title.color}">
                        ${title.title}
                    </div>
                    <p>축하합니다! 새로운 레벨에 도달했습니다!</p>
                    <button class="close-level-up-btn">계속하기</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 애니메이션 효과
        setTimeout(() => modal.classList.add('show'), 100);
        
        // 닫기 버튼 이벤트
        modal.querySelector('.close-level-up-btn').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => document.body.removeChild(modal), 300);
        });
        
        // 자동 닫기 (5초 후)
        setTimeout(() => {
            if (document.body.contains(modal)) {
                modal.classList.remove('show');
                setTimeout(() => document.body.removeChild(modal), 300);
            }
        }, 5000);
    }
    
    showAchievementNotification(achievement) {
        const notification = document.createElement('div');
        notification.className = 'achievement-notification';
        notification.innerHTML = `
            <div class="achievement-content">
                <div class="achievement-icon" style="background: ${achievement.color}">
                    ${achievement.icon}
                </div>
                <div class="achievement-text">
                    <h4>새로운 성취!</h4>
                    <h3>${achievement.name}</h3>
                    <p>${achievement.description}</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // 애니메이션 효과
        setTimeout(() => notification.classList.add('show'), 100);
        
        // 자동 제거 (4초 후)
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
    
    updateUI() {
        // 헤더 통계 업데이트
        const scoreElement = document.getElementById('user-score');
        const levelElement = document.getElementById('user-level');
        const accuracyElement = document.getElementById('user-accuracy');
        
        if (scoreElement) scoreElement.textContent = this.totalScore.toLocaleString();
        if (levelElement) levelElement.textContent = this.currentLevel;
        
        const stats = this.getPlayerStats();
        const accuracy = stats.questionsAnswered > 0 ? 
            Math.round((stats.correctAnswers / stats.questionsAnswered) * 100) : 0;
        if (accuracyElement) accuracyElement.textContent = `${accuracy}%`;
        
        // 진행률 바 업데이트
        this.updateProgressBar();
        
        // 타이틀 업데이트
        this.updateUserTitle();
    }
    
    updateProgressBar() {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        if (progressFill && progressText) {
            const progress = this.getExpProgress();
            progressFill.style.width = `${progress.percentage}%`;
            progressText.textContent = `${progress.current}/${progress.required} EXP`;
        }
    }
    
    updateUserTitle() {
        const title = this.getCurrentTitle();
        
        // 사용자 타이틀 표시 (헤더에 추가할 수 있음)
        let titleElement = document.getElementById('user-title');
        if (!titleElement) {
            titleElement = document.createElement('div');
            titleElement.id = 'user-title';
            titleElement.className = 'user-title';
            
            const userStats = document.querySelector('.user-stats');
            if (userStats) {
                userStats.appendChild(titleElement);
            }
        }
        
        titleElement.innerHTML = `
            <span class="title-icon">${title.icon}</span>
            <span class="title-text" style="color: ${title.color}">${title.title}</span>
        `;
    }
    
    getRecentAchievements() {
        // 최근 획득한 성취 배지들 반환 (최근 5개)
        return this.achievements.slice(-5).map(id => this.achievementDefinitions[id]);
    }
    
    getAllAchievements() {
        return this.achievements.map(id => this.achievementDefinitions[id]);
    }
    
    getAchievementProgress() {
        const total = Object.keys(this.achievementDefinitions).length;
        const earned = this.achievements.length;
        return {
            earned,
            total,
            percentage: Math.round((earned / total) * 100)
        };
    }
    
    // 데이터 저장/로드
    saveUserProgress() {
        const progressData = {
            level: this.currentLevel,
            exp: this.currentExp,
            totalScore: this.totalScore,
            achievements: this.achievements,
            streakCount: this.streakCount,
            maxStreak: this.maxStreak,
            lastSaved: new Date().toISOString()
        };
        
        localStorage.setItem('awsGameProgress', JSON.stringify(progressData));
    }
    
    loadUserProgress() {
        const savedData = localStorage.getItem('awsGameProgress');
        if (savedData) {
            try {
                const progressData = JSON.parse(savedData);
                this.currentLevel = progressData.level || 1;
                this.currentExp = progressData.exp || 0;
                this.totalScore = progressData.totalScore || 0;
                this.achievements = progressData.achievements || [];
                this.streakCount = progressData.streakCount || 0;
                this.maxStreak = progressData.maxStreak || 0;
            } catch (error) {
                console.error('Failed to load user progress:', error);
            }
        }
    }
    
    resetProgress() {
        this.currentLevel = 1;
        this.currentExp = 0;
        this.totalScore = 0;
        this.achievements = [];
        this.streakCount = 0;
        this.maxStreak = 0;
        
        localStorage.removeItem('awsGameProgress');
        this.updateUI();
    }
    
    // 리더보드용 데이터
    getLeaderboardData() {
        return {
            username: this.gameManager.currentUser?.username || 'Anonymous',
            level: this.currentLevel,
            totalScore: this.totalScore,
            achievements: this.achievements.length,
            accuracy: this.getPlayerStats().questionsAnswered > 0 ? 
                Math.round((this.getPlayerStats().correctAnswers / this.getPlayerStats().questionsAnswered) * 100) : 0,
            title: this.getCurrentTitle().title
        };
    }
}

// Export for use in other modules
window.LevelSystem = LevelSystem;
