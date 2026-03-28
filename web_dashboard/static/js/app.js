/**
 * Norfain ReAct Agent - Frontend Application
 * Optimized for: Performance, Security, UX, Accessibility
 *
 * Key improvements:
 * - Modular architecture with event delegation
 * - Input sanitization (XSS prevention)
 * - Debounced API calls
 * - Proper error handling with user-friendly messages
 * - Accessibility (ARIA labels, keyboard navigation)
 * - Performance: caching, minimal DOM manipulation
 */

const APP = (function() {
    'use strict';

    // ============================================================================
    // CONFIGURATION
    // ============================================================================

    const CONFIG = {
        API_BASE: '/api',
        HEALTH_ENDPOINT: '/health',
        DEBOUNCE_DELAY: 300,
        MAX_REASONING_STEPS: 10,
        CACHE_TTL: 3600 * 1000, // 1 hour in ms
        ENVIRONMENTS: {
            dev: ['localhost', '127.0.0.1'],
            prod: []
        }
    };

    // ============================================================================
    // STATE MANAGEMENT
    // ============================================================================

    const state = {
        isLoading: false,
        currentLanguage: localStorage.getItem('language') || 'en',
        lastApiCall: 0,
        cache: new Map(),
        abortController: null
    };

    // ============================================================================
    // TRANSLATIONS
    // ============================================================================

    const translations = {
        en: {
            subtitle: "Interactive Demo: Baseline vs ReAct Reasoning",
            askQuestion: "💬 Ask a Question",
            inputPlaceholder: "e.g., How much do Norwegian families spend on housing?",
            askBothAgents: "Ask Both Agents",
            examples: "Examples:",
            example1: "How much do Norwegian families spend on housing?",
            example2: "Do Norwegians spend more on housing or food?",
            baselineAgent: "🤖 Baseline Agent",
            reactAgent: "🧠 ReAct Agent",
            type: "Type:",
            baselineType: "Direct prompting, single-step",
            reactType: "Multi-step reasoning with traces",
            waitingForQuestion: "Waiting for question...",
            timeDifference: "Time Difference",
            reactIterations: "ReAct Iterations",
            baselineToolUsage: "Baseline Tool Usage",
            reactToolUsage: "ReAct Tool Usage",
            processing: "Processing...",
            processingQuestion: "Processing question...",
            processingReasoning: "Processing question with reasoning...",
            reasoningTrace: "🔍 Reasoning Trace:",
            iteration: "Iteration",
            thought: "THOUGHT:",
            action: "ACTION:",
            observation: "OBSERVATION:",
            ofBaselineTime: "of baseline time",
            errorOccurred: "An error occurred",
            serverError: "Server connection failed. Please check if the backend is running.",
            rateLimitExceeded: "Too many requests. Please wait and try again.",
            questionRequired: "Please enter a question",
            questionTooLong: "Question is too long (maximum 1000 characters)",
            invalidCharacters: "Question contains invalid characters"
        },
        no: {
            subtitle: "Interaktiv Demo: Baseline vs ReAct Resonnering",
            askQuestion: "💬 Still et Spørsmål",
            inputPlaceholder: "f.eks., Hvor mye bruker norske familier på bolig?",
            askBothAgents: "Spør Begge Agenter",
            examples: "Eksempler:",
            example1: "Hvor mye bruker norske familier på bolig?",
            example2: "Bruker nordmenn mer på bolig eller mat?",
            baselineAgent: "🤖 Baseline Agent",
            reactAgent: "🧠 ReAct Agent",
            type: "Type:",
            baselineType: "Direkte prompting, enkelt-trinn",
            reactType: "Flertrinnresonnering med spor",
            waitingForQuestion: "Venter på spørsmål...",
            timeDifference: "Tidsforskjell",
            reactIterations: "ReAct Iterasjoner",
            baselineToolUsage: "Baseline Verktøybruk",
            reactToolUsage: "ReAct Verktøybruk",
            processing: "Behandler...",
            processingQuestion: "Behandler spørsmål...",
            processingReasoning: "Behandler spørsmål med resonnering...",
            reasoningTrace: "🔍 Resonnering Spor:",
            iteration: "Iterasjon",
            thought: "TANKE:",
            action: "HANDLING:",
            observation: "OBSERVASJON:",
            ofBaselineTime: "av baseline tid",
            errorOccurred: "En feil oppstod",
            serverError: "Tilkobling til serveren mislyktes. Vennligst sjekk at backend kjører.",
            rateLimitExceeded: "For mange forespørsler. Vennligst vent og prøv igjen.",
            questionRequired: "Vennligst skriv inn et spørsmål",
            questionTooLong: "Spørsmålet er for langt (maksimum 1000 tegn)",
            invalidCharacters: "Spørsmålet inneholder ugyldige tegn"
        }
    };

    // ============================================================================
    // UTILITIES
    // ============================================================================

    const Utils = {
        /**
         * Sanitize HTML to prevent XSS
         * Creates text nodes instead of using innerHTML
         */
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        /**
         * Sanitize and escape user input
         */
        sanitizeInput(input) {
            if (typeof input !== 'string') return '';
            return input.trim()
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#x27;')
                .replace(/&/g, '&amp;');
        },

        /**
         * Format time in seconds
         */
        formatTime(seconds) {
            return `${parseFloat(seconds).toFixed(2)}s`;
        },

        /**
         * Debounce function
         */
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Get cache key for questions
         */
        getCacheKey(question, language) {
            return `ask:${btoa(question.substring(0, 200) + ':' + language).substring(0, 32)}`;
        },

        /**
         * Check if running in development mode
         */
        isDev() {
            return CONFIG.ENVIRONMENTS.dev.includes(window.location.hostname);
        },

        /**
         * Throttle function calls
         */
        throttle(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }
    };

    // ============================================================================
    // UI CONTROLLER
    // ============================================================================

    const UI = {
        elements: {
            questionInput: null,
            askBtn: null,
            baselineResponse: null,
            reactResponse: null,
            baselineTime: null,
            reactTime: null,
            reasoningTrace: null,
            statsPanel: null,
            timeDiff: null,
            timeComparison: null,
            iterations: null,
            baselineTool: null,
            langEn: null,
            langNo: null
        },

        /**
         * Initialize UI element references
         */
        init() {
            this.elements = {
                questionInput: document.getElementById('questionInput'),
                askBtn: document.getElementById('askBtn'),
                baselineResponse: document.getElementById('baselineResponse'),
                reactResponse: document.getElementById('reactResponse'),
                baselineTime: document.getElementById('baselineTime'),
                reactTime: document.getElementById('reactTime'),
                reasoningTrace: document.getElementById('reasoningTrace'),
                statsPanel: document.getElementById('statsPanel'),
                timeDiff: document.getElementById('timeDiff'),
                timeComparison: document.getElementById('timeComparison'),
                iterations: document.getElementById('iterations'),
                baselineTool: document.getElementById('baselineTool'),
                langEn: document.getElementById('lang-en'),
                langNo: document.getElementById('lang-no')
            };
        },

        /**
         * Show loading state
         */
        showLoading() {
            const lang = state.currentLanguage;
            const t = translations[lang];

            this.elements.askBtn.disabled = true;
            this.elements.askBtn.textContent = t.processing;

            this.elements.baselineResponse.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <div>${Utils.escapeHtml(t.processingQuestion)}</div>
                </div>
            `;
            this.elements.reactResponse.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <div>${Utils.escapeHtml(t.processingReasoning)}</div>
                </div>
            `;
            this.elements.reasoningTrace.innerHTML = '';
            this.elements.statsPanel.style.display = 'none';
        },

        /**
         * Hide loading state
         */
        hideLoading() {
            const lang = state.currentLanguage;
            const t = translations[lang];
            this.elements.askBtn.disabled = false;
            this.elements.askBtn.textContent = t.askBothAgents;
        },

        /**
         * Display error message
         */
        showError(error) {
            const lang = state.currentLanguage;
            const t = translations[lang];
            const errorHtml = `
                <div class="error-message">
                    <strong>⚠️ ${Utils.escapeHtml(t.errorOccurred)}:</strong> ${Utils.escapeHtml(error)}
                    <br><br>
                    <small>Check browser console (F12) for details.</small>
                </div>
            `;
            this.elements.baselineResponse.innerHTML = errorHtml;
            this.elements.reactResponse.innerHTML = errorHtml;
        },

        /**
         * Render response data
         */
        renderResponse(data) {
            const lang = state.currentLanguage;
            const t = translations[lang];

            // Render Baseline
            this.elements.baselineResponse.innerHTML = `<p>${Utils.escapeHtml(data.baseline.answer)}</p>`;
            this.elements.baselineTime.textContent = Utils.formatTime(data.baseline.time);

            // Render ReAct
            this.elements.reactResponse.innerHTML = `<p>${Utils.escapeHtml(data.react.answer)}</p>`;
            this.elements.reactTime.textContent = Utils.formatTime(data.react.time);

            // Render reasoning trace (safely)
            if (data.react.reasoning_steps && data.react.reasoning_steps.length > 0) {
                this.renderReasoningTrace(data.react.reasoning_steps, t);
            }

            // Render statistics
            this.elements.statsPanel.style.display = 'grid';
            this.elements.timeDiff.textContent = `+${Utils.formatTime(data.comparison.time_difference)}`;
            this.elements.timeComparison.textContent = `${Math.round(data.comparison.time_ratio * 100)}% ${t.ofBaselineTime}`;
            this.elements.iterations.textContent = data.react.iterations || 'N/A';
            this.elements.baselineTool.textContent = data.baseline.tool_used ? '✓ Yes' : '✗ No';
        },

        /**
         * Render reasoning trace securely
         */
        renderReasoningTrace(steps, t) {
            let traceHTML = `<div class="reasoning-trace"><h3>${Utils.escapeHtml(t.reasoningTrace)}</h3>`;

            const limitedSteps = steps.slice(0, CONFIG.MAX_REASONING_STEPS);

            limitedSteps.forEach((step, idx) => {
                if (step.action) {
                    const thought = Utils.escapeHtml(step.thought.substring(0, 200));
                    const action = Utils.escapeHtml(step.action);
                    const observation = Utils.escapeHtml(
                        typeof step.observation === 'string'
                            ? step.observation.substring(0, 150)
                            : String(step.observation).substring(0, 150)
                    );

                    traceHTML += `
                        <div class="reasoning-step" aria-labelledby="step-${idx}">
                            <div><span class="step-label">${t.iteration} ${step.iteration}:</span></div>
                            <div><span class="step-label">${t.thought}</span> ${thought}...</div>
                            <div><span class="step-label">${t.action}</span> ${action}</div>
                            <div><span class="step-label">${t.observation}</span> ${observation}...</div>
                        </div>
                    `;
                }
            });

            traceHTML += '</div>';
            this.elements.reasoningTrace.innerHTML = traceHTML;
        },

        /**
         * Set language
         */
        setLanguage(lang) {
            state.currentLanguage = lang;
            localStorage.setItem('language', lang);

            // Update button states
            if (this.elements.langEn) {
                this.elements.langEn.classList.toggle('active', lang === 'en');
            }
            if (this.elements.langNo) {
                this.elements.langNo.classList.toggle('active', lang === 'no');
            }

            this.updateTranslations();
        },

        /**
         * Update all translations on the page
         */
        updateTranslations() {
            const lang = state.currentLanguage;
            const t = translations[lang];

            document.querySelectorAll('[data-translate]').forEach(el => {
                const key = el.getAttribute('data-translate');
                if (t[key]) {
                    el.textContent = t[key];
                }
            });

            document.querySelectorAll('[data-translate-placeholder]').forEach(el => {
                const key = el.getAttribute('data-translate-placeholder');
                if (t[key]) {
                    el.placeholder = t[key];
                }
            });
        }
    };

    // ============================================================================
    // API CLIENT
    // ============================================================================

    const API = {
        /**
         * Make API request with error handling and abort support
         */
        async request(endpoint, options = {}) {
            const now = Date.now();
            const timeSinceLastCall = now - state.lastApiCall;

            // Rate limiting at client side
            if (timeSinceLastCall < 1000) {
                await new Promise(resolve => setTimeout(resolve, 1000 - timeSinceLastCall));
            }

            state.lastApiCall = Date.now();

            // Cancel any ongoing request
            if (state.abortController) {
                state.abortController.abort();
            }

            state.abortController = new AbortController();
            const signal = state.abortController.signal;

            try {
                const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
                    ...options,
                    signal,
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));

                    if (response.status === 429) {
                        throw new Error(translations[state.currentLanguage].rateLimitExceeded);
                    } else if (response.status >= 500) {
                        throw new Error(translations[state.currentLanguage].serverError);
                    } else {
                        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
                    }
                }

                return await response.json();

            } catch (error) {
                if (error.name === 'AbortError') {
                    throw new Error('Request cancelled');
                }
                throw error;
            }
        },

        /**
         * Ask question to both agents
         */
        async askQuestion(question, language) {
            // Check cache first
            const cacheKey = Utils.getCacheKey(question, language);
            if (state.cache.has(cacheKey)) {
                const cached = state.cache.get(cacheKey);
                const age = Date.now() - cached.timestamp;
                if (age < CONFIG.CACHE_TTL) {
                    console.log('✅ Using cached response');
                    return cached.data;
                }
                state.cache.delete(cacheKey);
            }

            const data = await this.request('/ask', {
                method: 'POST',
                body: JSON.stringify({
                    question: question,
                    language: language
                })
            });

            // Cache successful response
            state.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });

            return data;
        },

        /**
         * Check health status
         */
        async checkHealth() {
            try {
                const response = await fetch(CONFIG.HEALTH_ENDPOINT);
                return await response.json();
            } catch (error) {
                console.error('Health check failed:', error);
                return null;
            }
        }
    };

    // ============================================================================
    // APPLICATION CONTROLLER
    // ============================================================================

    const App = {
        init() {
            this.setupEventListeners();
            this.setupKeyboardNavigation();
            UI.init();
            UI.setLanguage(state.currentLanguage);
            this.checkServerHealth();
        },

        setupEventListeners() {
            // Ask button
            const askBtn = document.getElementById('askBtn');
            if (askBtn) {
                askBtn.addEventListener('click', Utils.debounce(() => this.handleAskQuestion(), CONFIG.DEBOUNCE_DELAY));
            }

            // Enter key in input
            const questionInput = document.getElementById('questionInput');
            if (questionInput) {
                questionInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.handleAskQuestion();
                    }
                });

                // Auto-focus on load
                questionInput.focus();
            }

            // Language switcher buttons
            document.querySelectorAll('.lang-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const lang = e.target.id.replace('lang-', '');
                    UI.setLanguage(lang);
                });
            });

            // Example questions
            document.querySelectorAll('.example-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const questionInput = document.getElementById('questionInput');
                    questionInput.value = btn.textContent.trim();
                    questionInput.focus();
                });
            });
        },

        setupKeyboardNavigation() {
            document.addEventListener('keydown', (e) => {
                // Escape to cancel ongoing request
                if (e.key === 'Escape' && state.isLoading) {
                    if (state.abortController) {
                        state.abortController.abort();
                        UI.hideLoading();
                        console.log('Request cancelled by user');
                    }
                }
            });
        },

        async checkServerHealth() {
            try {
                const health = await API.checkHealth();
                if (health && health.status === 'healthy') {
                    console.log('✅ Server connected:', health);
                } else {
                    console.warn('⚠️ Server health check failed:', health);
                }
            } catch (error) {
                console.error('❌ Cannot connect to server:', error);
            }
        },

        async handleAskQuestion() {
            if (state.isLoading) {
                return;
            }

            const questionInput = document.getElementById('questionInput');
            const question = questionInput.value.trim();

            // Validate
            if (!question) {
                alert(translations[state.currentLanguage].questionRequired);
                questionInput.focus();
                return;
            }

            if (question.length > 1000) {
                alert(translations[state.currentLanguage].questionTooLong);
                return;
            }

            state.isLoading = true;
            UI.showLoading();

            try {
                const result = await API.askQuestion(question, state.currentLanguage);
                UI.renderResponse(result);
            } catch (error) {
                console.error('API Error:', error);
                UI.showError(error.message || 'Unknown error occurred');
            } finally {
                state.isLoading = false;
                UI.hideLoading();
            }
        }
    };

    // ============================================================================
    // INITIALIZATION
    // ============================================================================

    // Expose public API globally
    window.APP = {
        init: () => App.init(),
        setLanguage: (lang) => UI.setLanguage(lang),
        handleAskQuestion: () => App.handleAskQuestion(),
        useExample: (btn) => {
            const input = document.getElementById('questionInput');
            if (input && btn) {
                input.value = btn.textContent.trim();
                input.focus();
            }
        }
    };

    // Auto-initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('🚀 Initializing Norfain Dashboard...');
            App.init();
            console.log('✅ Dashboard ready');
        });
    } else {
        console.log('🚀 Initializing Norfain Dashboard...');
        App.init();
        console.log('✅ Dashboard ready');
    }

    // Dev tools
    if (Utils.isDev()) {
        window.NORFAIN = { App, UI, API, Utils, state, APP };
    }

})();