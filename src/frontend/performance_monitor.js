/**
 * AWS Problem Solver Game - Performance Monitor
 * 성능 모니터링 및 최적화 도구
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            loadTimes: {},
            apiCalls: {},
            userInteractions: {},
            memoryUsage: {},
            errors: []
        };
        
        this.observers = {};
        this.isMonitoring = false;
        
        this.init();
    }
    
    init() {
        this.setupPerformanceObservers();
        this.setupErrorTracking();
        this.startMonitoring();
    }
    
    setupPerformanceObservers() {
        // Navigation Timing API
        if ('performance' in window && 'getEntriesByType' in performance) {
            this.observeNavigationTiming();
        }
        
        // Resource Timing API
        if ('PerformanceObserver' in window) {
            this.observeResourceTiming();
            this.observeUserTiming();
            this.observeLongTasks();
        }
        
        // Memory API (Chrome only)
        if ('memory' in performance) {
            this.observeMemoryUsage();
        }
    }
    
    observeNavigationTiming() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            this.metrics.loadTimes.navigation = {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                domInteractive: navigation.domInteractive - navigation.navigationStart,
                firstPaint: this.getFirstPaint(),
                firstContentfulPaint: this.getFirstContentfulPaint()
            };
        }
    }
    
    observeResourceTiming() {
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                if (entry.entryType === 'resource') {
                    this.recordResourceTiming(entry);
                }
            });
        });
        
        observer.observe({ entryTypes: ['resource'] });
        this.observers.resource = observer;
    }
    
    observeUserTiming() {
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                if (entry.entryType === 'measure') {
                    this.recordUserTiming(entry);
                }
            });
        });
        
        observer.observe({ entryTypes: ['measure'] });
        this.observers.userTiming = observer;
    }
    
    observeLongTasks() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    list.getEntries().forEach(entry => {
                        if (entry.entryType === 'longtask') {
                            this.recordLongTask(entry);
                        }
                    });
                });
                
                observer.observe({ entryTypes: ['longtask'] });
                this.observers.longTask = observer;
            } catch (e) {
                // Long Task API not supported
                console.warn('Long Task API not supported');
            }
        }
    }
    
    observeMemoryUsage() {
        setInterval(() => {
            if (performance.memory) {
                this.metrics.memoryUsage[Date.now()] = {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize,
                    jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                };
            }
        }, 5000); // Every 5 seconds
    }
    
    setupErrorTracking() {
        window.addEventListener('error', (event) => {
            this.recordError({
                type: 'javascript',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error ? event.error.stack : null,
                timestamp: Date.now()
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.recordError({
                type: 'promise',
                message: event.reason.message || event.reason,
                stack: event.reason.stack,
                timestamp: Date.now()
            });
        });
    }
    
    // Performance Measurement Methods
    startTiming(label) {
        performance.mark(`${label}-start`);
    }
    
    endTiming(label) {
        performance.mark(`${label}-end`);
        performance.measure(label, `${label}-start`, `${label}-end`);
    }
    
    recordAPICall(url, method, startTime, endTime, status) {
        const duration = endTime - startTime;
        const key = `${method} ${url}`;
        
        if (!this.metrics.apiCalls[key]) {
            this.metrics.apiCalls[key] = {
                count: 0,
                totalDuration: 0,
                avgDuration: 0,
                minDuration: Infinity,
                maxDuration: 0,
                errors: 0
            };
        }
        
        const apiMetric = this.metrics.apiCalls[key];
        apiMetric.count++;
        apiMetric.totalDuration += duration;
        apiMetric.avgDuration = apiMetric.totalDuration / apiMetric.count;
        apiMetric.minDuration = Math.min(apiMetric.minDuration, duration);
        apiMetric.maxDuration = Math.max(apiMetric.maxDuration, duration);
        
        if (status >= 400) {
            apiMetric.errors++;
        }
    }
    
    recordUserInteraction(type, element, duration = 0) {
        const timestamp = Date.now();
        
        if (!this.metrics.userInteractions[type]) {
            this.metrics.userInteractions[type] = [];
        }
        
        this.metrics.userInteractions[type].push({
            element: element.tagName || element,
            duration,
            timestamp
        });
    }
    
    recordResourceTiming(entry) {
        const resourceType = this.getResourceType(entry.name);
        
        if (!this.metrics.loadTimes[resourceType]) {
            this.metrics.loadTimes[resourceType] = [];
        }
        
        this.metrics.loadTimes[resourceType].push({
            name: entry.name,
            duration: entry.duration,
            size: entry.transferSize || 0,
            cached: entry.transferSize === 0 && entry.decodedBodySize > 0
        });
    }
    
    recordUserTiming(entry) {
        if (!this.metrics.userInteractions.customTimings) {
            this.metrics.userInteractions.customTimings = {};
        }
        
        this.metrics.userInteractions.customTimings[entry.name] = {
            duration: entry.duration,
            startTime: entry.startTime
        };
    }
    
    recordLongTask(entry) {
        if (!this.metrics.userInteractions.longTasks) {
            this.metrics.userInteractions.longTasks = [];
        }
        
        this.metrics.userInteractions.longTasks.push({
            duration: entry.duration,
            startTime: entry.startTime,
            attribution: entry.attribution
        });
    }
    
    recordError(error) {
        this.metrics.errors.push(error);
        
        // Keep only last 50 errors
        if (this.metrics.errors.length > 50) {
            this.metrics.errors = this.metrics.errors.slice(-50);
        }
    }
    
    // Helper Methods
    getResourceType(url) {
        if (url.includes('.js')) return 'javascript';
        if (url.includes('.css')) return 'stylesheet';
        if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/i)) return 'image';
        if (url.includes('.woff') || url.includes('.ttf')) return 'font';
        return 'other';
    }
    
    getFirstPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
        return firstPaint ? firstPaint.startTime : null;
    }
    
    getFirstContentfulPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
        return fcp ? fcp.startTime : null;
    }
    
    // Analysis Methods
    analyzePerformance() {
        const analysis = {
            loadPerformance: this.analyzeLoadPerformance(),
            apiPerformance: this.analyzeAPIPerformance(),
            userExperience: this.analyzeUserExperience(),
            memoryUsage: this.analyzeMemoryUsage(),
            errors: this.analyzeErrors(),
            recommendations: []
        };
        
        analysis.recommendations = this.generateRecommendations(analysis);
        
        return analysis;
    }
    
    analyzeLoadPerformance() {
        const navigation = this.metrics.loadTimes.navigation;
        if (!navigation) return null;
        
        return {
            domContentLoaded: navigation.domContentLoaded,
            loadComplete: navigation.loadComplete,
            domInteractive: navigation.domInteractive,
            firstPaint: navigation.firstPaint,
            firstContentfulPaint: navigation.firstContentfulPaint,
            score: this.calculateLoadScore(navigation)
        };
    }
    
    analyzeAPIPerformance() {
        const apiCalls = this.metrics.apiCalls;
        const analysis = {};
        
        Object.keys(apiCalls).forEach(key => {
            const metric = apiCalls[key];
            analysis[key] = {
                ...metric,
                errorRate: metric.count > 0 ? (metric.errors / metric.count) * 100 : 0,
                performance: this.categorizeAPIPerformance(metric.avgDuration)
            };
        });
        
        return analysis;
    }
    
    analyzeUserExperience() {
        const interactions = this.metrics.userInteractions;
        
        return {
            totalInteractions: this.countTotalInteractions(interactions),
            longTasks: interactions.longTasks || [],
            customTimings: interactions.customTimings || {},
            responsiveness: this.calculateResponsiveness(interactions)
        };
    }
    
    analyzeMemoryUsage() {
        const memoryData = Object.values(this.metrics.memoryUsage);
        if (memoryData.length === 0) return null;
        
        const latest = memoryData[memoryData.length - 1];
        const initial = memoryData[0];
        
        return {
            current: latest,
            growth: latest.usedJSHeapSize - initial.usedJSHeapSize,
            utilizationRate: (latest.usedJSHeapSize / latest.jsHeapSizeLimit) * 100,
            trend: this.calculateMemoryTrend(memoryData)
        };
    }
    
    analyzeErrors() {
        const errors = this.metrics.errors;
        const errorTypes = {};
        
        errors.forEach(error => {
            if (!errorTypes[error.type]) {
                errorTypes[error.type] = 0;
            }
            errorTypes[error.type]++;
        });
        
        return {
            total: errors.length,
            types: errorTypes,
            recent: errors.slice(-10),
            errorRate: this.calculateErrorRate()
        };
    }
    
    generateRecommendations(analysis) {
        const recommendations = [];
        
        // Load Performance Recommendations
        if (analysis.loadPerformance) {
            if (analysis.loadPerformance.domContentLoaded > 2000) {
                recommendations.push({
                    type: 'performance',
                    priority: 'high',
                    message: 'DOM 로딩 시간이 2초를 초과합니다. JavaScript 최적화를 고려하세요.',
                    action: 'optimize-js'
                });
            }
            
            if (analysis.loadPerformance.firstContentfulPaint > 1500) {
                recommendations.push({
                    type: 'performance',
                    priority: 'medium',
                    message: 'First Contentful Paint가 1.5초를 초과합니다. 중요한 리소스의 우선순위를 높이세요.',
                    action: 'optimize-critical-resources'
                });
            }
        }
        
        // API Performance Recommendations
        Object.keys(analysis.apiPerformance).forEach(api => {
            const perf = analysis.apiPerformance[api];
            
            if (perf.avgDuration > 3000) {
                recommendations.push({
                    type: 'api',
                    priority: 'high',
                    message: `API ${api}의 평균 응답 시간이 3초를 초과합니다.`,
                    action: 'optimize-api'
                });
            }
            
            if (perf.errorRate > 5) {
                recommendations.push({
                    type: 'reliability',
                    priority: 'high',
                    message: `API ${api}의 오류율이 ${perf.errorRate.toFixed(1)}%입니다.`,
                    action: 'fix-api-errors'
                });
            }
        });
        
        // Memory Usage Recommendations
        if (analysis.memoryUsage) {
            if (analysis.memoryUsage.utilizationRate > 80) {
                recommendations.push({
                    type: 'memory',
                    priority: 'high',
                    message: '메모리 사용률이 80%를 초과합니다. 메모리 누수를 확인하세요.',
                    action: 'check-memory-leaks'
                });
            }
            
            if (analysis.memoryUsage.growth > 50 * 1024 * 1024) { // 50MB
                recommendations.push({
                    type: 'memory',
                    priority: 'medium',
                    message: '메모리 사용량이 50MB 이상 증가했습니다.',
                    action: 'optimize-memory-usage'
                });
            }
        }
        
        // Error Recommendations
        if (analysis.errors.total > 10) {
            recommendations.push({
                type: 'reliability',
                priority: 'high',
                message: `${analysis.errors.total}개의 오류가 발생했습니다.`,
                action: 'fix-errors'
            });
        }
        
        return recommendations;
    }
    
    // Utility Methods
    calculateLoadScore(navigation) {
        let score = 100;
        
        if (navigation.domContentLoaded > 2000) score -= 20;
        if (navigation.loadComplete > 4000) score -= 20;
        if (navigation.firstContentfulPaint > 1500) score -= 15;
        if (navigation.domInteractive > 3000) score -= 15;
        
        return Math.max(0, score);
    }
    
    categorizeAPIPerformance(avgDuration) {
        if (avgDuration < 500) return 'excellent';
        if (avgDuration < 1000) return 'good';
        if (avgDuration < 2000) return 'fair';
        return 'poor';
    }
    
    countTotalInteractions(interactions) {
        let total = 0;
        Object.keys(interactions).forEach(key => {
            if (Array.isArray(interactions[key])) {
                total += interactions[key].length;
            }
        });
        return total;
    }
    
    calculateResponsiveness(interactions) {
        const longTasks = interactions.longTasks || [];
        const totalLongTaskTime = longTasks.reduce((sum, task) => sum + task.duration, 0);
        
        if (longTasks.length === 0) return 'excellent';
        if (totalLongTaskTime < 100) return 'good';
        if (totalLongTaskTime < 300) return 'fair';
        return 'poor';
    }
    
    calculateMemoryTrend(memoryData) {
        if (memoryData.length < 2) return 'stable';
        
        const recent = memoryData.slice(-5);
        const growth = recent[recent.length - 1].usedJSHeapSize - recent[0].usedJSHeapSize;
        
        if (growth > 10 * 1024 * 1024) return 'increasing'; // 10MB
        if (growth < -5 * 1024 * 1024) return 'decreasing'; // -5MB
        return 'stable';
    }
    
    calculateErrorRate() {
        const now = Date.now();
        const oneHourAgo = now - (60 * 60 * 1000);
        const recentErrors = this.metrics.errors.filter(error => error.timestamp > oneHourAgo);
        
        return recentErrors.length;
    }
    
    // Public API
    startMonitoring() {
        this.isMonitoring = true;
        console.log('Performance monitoring started');
    }
    
    stopMonitoring() {
        this.isMonitoring = false;
        
        // Disconnect observers
        Object.values(this.observers).forEach(observer => {
            if (observer && observer.disconnect) {
                observer.disconnect();
            }
        });
        
        console.log('Performance monitoring stopped');
    }
    
    getMetrics() {
        return this.metrics;
    }
    
    getReport() {
        return {
            timestamp: Date.now(),
            metrics: this.metrics,
            analysis: this.analyzePerformance()
        };
    }
    
    exportReport() {
        const report = this.getReport();
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance-report-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
    }
    
    clearMetrics() {
        this.metrics = {
            loadTimes: {},
            apiCalls: {},
            userInteractions: {},
            memoryUsage: {},
            errors: []
        };
    }
}

// Monkey patch fetch for API monitoring
if (typeof window !== 'undefined' && window.fetch) {
    const originalFetch = window.fetch;
    
    window.fetch = function(...args) {
        const startTime = performance.now();
        const url = args[0];
        const options = args[1] || {};
        const method = options.method || 'GET';
        
        return originalFetch.apply(this, args)
            .then(response => {
                const endTime = performance.now();
                
                if (window.performanceMonitor) {
                    window.performanceMonitor.recordAPICall(
                        url, method, startTime, endTime, response.status
                    );
                }
                
                return response;
            })
            .catch(error => {
                const endTime = performance.now();
                
                if (window.performanceMonitor) {
                    window.performanceMonitor.recordAPICall(
                        url, method, startTime, endTime, 0
                    );
                }
                
                throw error;
            });
    };
}

// Export for use in other modules
window.PerformanceMonitor = PerformanceMonitor;
