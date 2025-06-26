/**
 * AWS Problem Solver Game - Configuration
 * 환경별 설정 관리
 */

class GameConfig {
    constructor() {
        // 환경 감지
        this.environment = this.detectEnvironment();
        
        // 기본 설정
        this.config = {
            // API 설정
            api: {
                baseUrl: this.getApiBaseUrl(),
                timeout: 30000,
                retryAttempts: 3
            },
            
            // 게임 설정
            game: {
                defaultTimeLimit: 60,
                maxHints: 3,
                hintPenalty: 10,
                maxLevel: 20
            },
            
            // UI 설정
            ui: {
                typingSpeed: 50,
                animationDuration: 300,
                notificationDuration: 3000
            },
            
            // 성능 설정
            performance: {
                enableMonitoring: this.environment !== 'production',
                enableDebugMode: this.environment === 'development',
                cacheTimeout: this.environment === 'production' ? 3600000 : 300000 // 1시간 vs 5분
            },
            
            // 기능 플래그
            features: {
                amazonQEnabled: false, // 배포 후 설정
                enhancedMonitoring: this.environment === 'production',
                debugConsole: this.environment !== 'production'
            }
        };
    }
    
    detectEnvironment() {
        const hostname = window.location.hostname;
        
        // 로컬 개발 환경
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        }
        
        // 개발 서버 (dev- 접두사 또는 .dev. 포함)
        if (hostname.includes('dev-') || hostname.includes('.dev.')) {
            return 'development';
        }
        
        // 스테이징 서버
        if (hostname.includes('staging') || hostname.includes('test')) {
            return 'staging';
        }
        
        // 프로덕션 (기본값)
        return 'production';
    }
    
    getApiBaseUrl() {
        // 환경별 API URL 설정
        const hostname = window.location.hostname;
        
        // 로컬 개발 환경
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:3000/dev';
        }
        
        // 배포된 환경에서는 런타임에 설정됨
        // deploy.sh에서 실제 API Gateway URL로 교체됨
        return window.AWS_GAME_CONFIG?.apiUrl || 'API_GATEWAY_URL_PLACEHOLDER';
    }
    
    // 설정 값 가져오기
    get(path) {
        return this.getNestedValue(this.config, path);
    }
    
    // 중첩된 객체에서 값 가져오기 (예: 'api.baseUrl')
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : null;
        }, obj);
    }
    
    // 설정 값 설정하기
    set(path, value) {
        this.setNestedValue(this.config, path, value);
    }
    
    // 중첩된 객체에 값 설정하기
    setNestedValue(obj, path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!current[key]) current[key] = {};
            return current[key];
        }, obj);
        target[lastKey] = value;
    }
    
    // 환경별 설정 오버라이드
    overrideForEnvironment(overrides) {
        if (overrides[this.environment]) {
            this.deepMerge(this.config, overrides[this.environment]);
        }
    }
    
    // 깊은 병합
    deepMerge(target, source) {
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                if (!target[key]) target[key] = {};
                this.deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        }
    }
    
    // 디버그 정보 출력
    debug() {
        if (this.get('features.debugConsole')) {
            console.group('🎮 AWS Problem Solver Game - Configuration');
            console.log('Environment:', this.environment);
            console.log('API Base URL:', this.get('api.baseUrl'));
            console.log('Features:', this.get('features'));
            console.log('Full Config:', this.config);
            console.groupEnd();
        }
    }
    
    // 런타임 설정 업데이트 (배포 후 실제 값으로 업데이트)
    updateRuntimeConfig(runtimeConfig) {
        if (runtimeConfig.apiUrl) {
            this.set('api.baseUrl', runtimeConfig.apiUrl);
        }
        
        if (runtimeConfig.features) {
            Object.keys(runtimeConfig.features).forEach(feature => {
                this.set(`features.${feature}`, runtimeConfig.features[feature]);
            });
        }
        
        // 설정 업데이트 후 디버그 정보 출력
        this.debug();
    }
}

// 전역 설정 인스턴스 생성
window.gameConfig = new GameConfig();

// 런타임 설정이 있다면 적용
if (window.AWS_GAME_CONFIG) {
    window.gameConfig.updateRuntimeConfig(window.AWS_GAME_CONFIG);
}

// 디버그 정보 출력
window.gameConfig.debug();

// ES6 모듈로도 사용 가능하도록 export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GameConfig;
}
