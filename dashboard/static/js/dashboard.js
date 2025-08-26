/**
 * Complete Dashboard JavaScript
 * Handles all dashboard functionality including real-time updates, orchestration, and conversational AI
 */

class Dashboard {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentIntent = null;
        this.industryConfigs = null;
        this.currentReportFilename = null;
        
        this.init();
    }

    async init() {
        console.log('Initializing dashboard...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup conversational AI
        this.setupConversationalAI();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Load initial data
        await this.loadInitialData();
        
        console.log('Dashboard initialized successfully');
    }

    // WebSocket Management
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.addActivityItem('🔗 Real-time connection established', 'status-online');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.addActivityItem('🔌 Connection lost - attempting to reconnect...', 'status-offline');
                this.attemptReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.addActivityItem('❌ Connection error', 'status-error');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.addActivityItem('❌ Failed to establish real-time connection', 'status-error');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.addActivityItem('❌ Failed to reconnect - please refresh the page', 'status-error');
        }
    }

    handleWebSocketMessage(data) {
        console.log('WebSocket message received:', data);
        
        switch (data.type) {
            case 'discovery_started':
                this.addActivityItem(`🚀 Discovery started for ${data.industry || 'organizations'} in ${data.region || 'all regions'}`, 'status-processing');
                break;
                
            case 'discovery_progress':
                this.updateDiscoveryProgress(data);
                break;
                
            case 'discovery_completed':
                this.handleDiscoveryCompleted(data);
                break;
                
            case 'discovery_error':
                this.addActivityItem(`❌ Discovery error: ${data.error}`, 'status-error');
                break;
                
            case 'workflow_created':
                this.addActivityItem(`📋 Workflow created: ${data.name}`, 'status-processing');
                break;
                
            case 'workflow_started':
                this.addActivityItem(`▶️ Workflow started: ${data.name}`, 'status-processing');
                break;
                
            case 'workflow_completed':
                this.addActivityItem(`✅ Workflow completed: ${data.name} (${data.execution_time}s)`, 'status-online');
                this.loadReports();
                break;
                
            case 'workflow_failed':
                this.addActivityItem(`❌ Workflow failed: ${data.error}`, 'status-error');
                break;
                
            case 'task_started':
                this.addActivityItem(`🔄 Task started: ${data.task_name}`, 'status-processing');
                break;
                
            case 'task_completed':
                this.addActivityItem(`✅ Task completed: ${data.task_name} (${data.execution_time}s)`, 'status-online');
                break;
                
            case 'task_failed':
                this.addActivityItem(`❌ Task failed: ${data.task_name} - ${data.error}`, 'status-error');
                break;
                
            case 'intent_execution_started':
                this.handleIntentExecutionUpdate(data);
                break;
                
            case 'intent_execution_completed':
                this.handleIntentExecutionUpdate(data);
                break;
                
            case 'intent_execution_failed':
                this.handleIntentExecutionUpdate(data);
                break;
                
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    // Data Loading Methods
   async loadInitialData() {
    try {
        console.log('Loading initial data...');
        
        // Load industry configurations first (most important)
        await this.loadWithRetry(
            () => this.loadIndustryConfigs(), 
            'Industry Configurations', 
            2
        );
        
        // Load saved configuration (doesn't require API)
        this.loadSavedConfig();
        
        // Load basic stats with fallback
        await this.loadWithRetry(
            async () => {
                const statsResponse = await fetch('/api/stats');
                if (statsResponse.ok) {
                    const stats = await statsResponse.json();
                    this.updateStats(stats);
                } else {
                    throw new Error(`Stats API returned ${statsResponse.status}`);
                }
            },
            'Statistics',
            2
        );
        
        // Load top associations with fallback
        await this.loadWithRetry(
            async () => {
                const associationsResponse = await fetch('/api/associations?limit=10');
                if (associationsResponse.ok) {
                    const associations = await associationsResponse.json();
                    this.updateTopAssociations(associations.associations || []);
                } else {
                    throw new Error(`Associations API returned ${associationsResponse.status}`);
                }
            },
            'Associations Data',
            2
        );
        
        // Load optional features (don't fail if these aren't available)
        const optionalLoaders = [
            { fn: () => this.loadReports(), name: 'Reports' },
            { fn: () => this.loadReportsViewer(), name: 'Reports Viewer' },
            { fn: () => this.loadARCReturns(), name: 'ARC Returns' },
            { fn: () => this.loadComprehensiveInsights(), name: 'Comprehensive Insights' },
            { fn: () => this.loadMarketIntelligence(), name: 'Market Intelligence' }
        ];
        
        for (const loader of optionalLoaders) {
            try {
                await loader.fn();
                this.addActivityItem(`✅ ${loader.name} loaded`, 'status-online');
            } catch (error) {
                console.warn(`${loader.name} not available:`, error);
                this.addActivityItem(`ℹ️ ${loader.name} not available yet`, 'status-processing');
            }
        }
        
        console.log('Initial data loading completed');
        
    } catch (error) {
        console.error('Critical error loading initial data:', error);
        this.addActivityItem('⚠️ Some dashboard features may be limited', 'status-error');
    }
}

// Add this new method for market intelligence
async loadMarketIntelligence() {
    try {
        const marketResponse = await fetch('/api/market-intelligence');
        if (marketResponse.ok) {
            const marketData = await marketResponse.json();
            this.updateMarketIntelligence(marketData);
        } else {
            throw new Error(`Market intelligence API returned ${marketResponse.status}`);
        }
    } catch (error) {
        console.log('Market intelligence not available:', error);
        throw error; // Re-throw so the caller knows it failed
    }
}

// Add these methods to the Dashboard class

// Voice Interface Integration
initVoiceInterface() {
    console.log('Initializing voice interface integration...');
    
    // Wait for voice interface to be ready
    const checkVoiceInterface = () => {
        if (window.voiceInterface && window.voiceInterface.isVoiceSupported()) {
            this.setupVoiceIntegration();
        } else {
            setTimeout(checkVoiceInterface, 500);
        }
    };
    
    checkVoiceInterface();
}

setupVoiceIntegration() {
    console.log('Setting up voice interface integration...');
    
    // Override the voice interface's sendVoiceMessageToDashboard method
    if (window.voiceInterface) {
        const originalMethod = window.voiceInterface.sendVoiceMessageToDashboard;
        
        window.voiceInterface.sendVoiceMessageToDashboard = async (transcript) => {
            try {
                this.showVoiceStatus('Processing...', 'processing');
                
                // Add voice message to chat
                this.addChatMessage(transcript, 'user', null, 'voice');
                
                // Send to dashboard AI controller
                const response = await fetch('/api/dashboard-ai/process-request', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: transcript,
                        context: {
                            input_method: 'voice',
                            timestamp: new Date().toISOString(),
                            voice_settings: window.voiceInterface.settings,
                            dashboard_state: this.getDashboardState()
                        }
                    })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    this.showVoiceError(`Error: ${result.error}`);
                    this.addChatMessage(`Error: ${result.error}`, 'ai', 'error');
                    return;
                }
                
                // Handle different types of responses
                this.handleAIResponse(result, transcript);
                
                this.showVoiceStatus('Ready', 'ready');
                
            } catch (error) {
                console.error('Error sending voice message:', error);
                this.showVoiceError('Failed to process voice message');
                this.addChatMessage('Sorry, I encountered an error processing your voice message.', 'ai', 'error');
            }
        };
    }
    
    // Add voice-specific chat message handling
    this.setupVoiceChatIntegration();
}

handleAIResponse(result, originalMessage) {
    console.log('Handling AI response:', result);
    
    // Add main response to chat
    this.addChatMessage(result.message, 'ai', null, 'ai-response');
    
    // Handle specific response types
    if (result.summary) {
        this.displayResponseSummary(result.summary);
    }
    
    if (result.generated_files && result.generated_files.length > 0) {
        this.displayGeneratedFiles(result.generated_files);
    }
    
    if (result.next_steps && result.next_steps.length > 0) {
        this.displayNextSteps(result.next_steps);
    }
    
    if (result.integration_instructions && result.integration_instructions.length > 0) {
        this.displayIntegrationInstructions(result.integration_instructions);
    }
    
    // Speak response if auto-speak is enabled
    if (window.voiceInterface && window.voiceInterface.settings.autoSpeak) {
        const voiceResponse = result.voice_response || this.extractTextFromHTML(result.message);
        if (voiceResponse) {
            window.voiceInterface.speak(voiceResponse);
        }
    }
    
    // Show follow-up questions
    if (result.follow_up_questions && result.follow_up_questions.length > 0) {
        this.displayFollowUpQuestions(result.follow_up_questions);
    }
}

displayResponseSummary(summary) {
    const summaryHtml = `
        <div class="ai-response-summary">
            <h4><i class="fas fa-chart-line"></i> Summary</h4>
            <div class="summary-stats">
                ${summary.actions_taken ? `<div class="stat-item">
                    <span class="stat-label">Actions Taken:</span>
                    <span class="stat-value">${summary.actions_taken.length}</span>
                </div>` : ''}
                ${summary.components_created ? `<div class="stat-item">
                    <span class="stat-label">Components Created:</span>
                    <span class="stat-value">${summary.components_created}</span>
                </div>` : ''}
                ${summary.endpoints_created ? `<div class="stat-item">
                    <span class="stat-label">Endpoints Created:</span>
                    <span class="stat-value">${summary.endpoints_created}</span>
                </div>` : ''}
                ${summary.agents_created ? `<div class="stat-item">
                    <span class="stat-label">Agents Created:</span>
                    <span class="stat-value">${summary.agents_created}</span>
                </div>` : ''}
            </div>
        </div>
    `;
    
    this.addChatMessage(summaryHtml, 'ai', null, 'summary');
}

displayGeneratedFiles(files) {
    const filesHtml = `
        <div class="generated-files">
            <h4><i class="fas fa-file-code"></i> Generated Files</h4>
            <div class="files-list">
                ${files.map(file => `
                    <div class="file-item">
                        <div class="file-info">
                            <i class="fas fa-${this.getFileIcon(file.type)}"></i>
                            <div class="file-details">
                                <div class="file-name">${file.name}</div>
                                <div class="file-description">${file.description}</div>
                                <div class="file-path">${file.path}</div>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button class="btn btn-sm btn-outline-primary" onclick="dashboard.viewGeneratedFile('${file.path}')">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="dashboard.downloadGeneratedFile('${file.path}')">
                                <i class="fas fa-download"></i> Download
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    this.addChatMessage(filesHtml, 'ai', null, 'generated-files');
}

displayNextSteps(steps) {
    const stepsHtml = `
        <div class="next-steps">
            <h4><i class="fas fa-list-check"></i> Next Steps</h4>
            <ol class="steps-list">
                ${steps.map(step => `<li class="step-item">${step}</li>`).join('')}
            </ol>
        </div>
    `;
    
    this.addChatMessage(stepsHtml, 'ai', null, 'next-steps');
}

displayIntegrationInstructions(instructions) {
    const instructionsHtml = `
        <div class="integration-instructions">
            <h4><i class="fas fa-puzzle-piece"></i> Integration Instructions</h4>
            <div class="instructions-list">
                ${instructions.map((instruction, index) => `
                    <div class="instruction-item">
                        <div class="instruction-number">${index + 1}</div>
                        <div class="instruction-text">${instruction}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    this.addChatMessage(instructionsHtml, 'ai', null, 'integration-instructions');
}

displayFollowUpQuestions(questions) {
    const questionsHtml = `
        <div class="follow-up-questions">
            <h4><i class="fas fa-question-circle"></i> Follow-up Questions</h4>
            <div class="questions-list">
                ${questions.map(question => `
                    <button class="follow-up-question-btn" onclick="dashboard.askFollowUpQuestion('${question.replace(/'/g, "\\'")}')">
                        ${question}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    this.addChatMessage(questionsHtml, 'ai', null, 'follow-up-questions');
}

askFollowUpQuestion(question) {
    // Add question to chat and process it
    this.addChatMessage(question, 'user');
    
    if (window.voiceInterface) {
        window.voiceInterface.sendVoiceMessageToDashboard(question);
    }
}

// Enhanced chat message method with voice support
addChatMessage(message, sender, type = null, messageClass = null) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message ${type ? `message-${type}` : ''} ${messageClass ? messageClass : ''}`;
    
    const timestamp = new Date().toLocaleTimeString();
    const senderIcon = sender === 'user' ? 'fa-user' : 'fa-robot';
    const senderLabel = sender === 'user' ? 'You' : 'AI Assistant';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <i class="fas ${senderIcon}"></i>
            <span class="sender-name">${senderLabel}</span>
            <span class="message-timestamp">${timestamp}</span>
            ${sender === 'ai' ? `
                <div class="message-actions">
                    <button class="message-action-btn" onclick="dashboard.speakMessage(this)" title="Speak this message">
                        <i class="fas fa-volume-up"></i>
                    </button>
                    <button class="message-action-btn" onclick="dashboard.copyMessage(this)" title="Copy message">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
            ` : ''}
        </div>
        <div class="message-content">${message}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add animation
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    requestAnimationFrame(() => {
        messageDiv.style.transition = 'all 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    });
}

speakMessage(button) {
    if (!window.voiceInterface) return;
    
    const messageContent = button.closest('.chat-message').querySelector('.message-content');
    const text = this.extractTextFromHTML(messageContent.innerHTML);
    
    window.voiceInterface.speak(text);
}

copyMessage(button) {
    const messageContent = button.closest('.chat-message').querySelector('.message-content');
    const text = this.extractTextFromHTML(messageContent.innerHTML);
    
    navigator.clipboard.writeText(text).then(() => {
        this.showNotification('Message copied to clipboard', 'success');
    }).catch(err => {
        console.error('Failed to copy message:', err);
        this.showNotification('Failed to copy message', 'error');
    });
}

// Utility methods
getDashboardState() {
    return {
        current_page: 'dashboard',
        active_workflows: this.activeWorkflows || [],
        recent_activities: this.recentActivities || [],
        loaded_data: {
            associations: !!this.associations,
            reports: !!this.reports,
            industry_configs: !!this.industryConfigs
        }
    };
}

getFileIcon(fileType) {
    const icons = {
        'component': 'file-code',
        'endpoint': 'server',
        'agent': 'robot',
        'database': 'database',
        'config': 'cog',
        'report': 'file-alt',
        'html': 'file-code',
        'css': 'palette',
        'javascript': 'file-code',
        'python': 'snake',
        'json': 'file-code'
    };
    
    return icons[fileType] || 'file';
}

extractTextFromHTML(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
}

showVoiceStatus(message, type) {
    if (window.voiceInterface) {
        window.voiceInterface.showVoiceStatus(message, type);
    }
}

showVoiceError(message) {
    if (window.voiceInterface) {
        window.voiceInterface.showVoiceError(message);
    }
}

// File management methods
async viewGeneratedFile(filePath) {
    try {
        const response = await fetch(`/api/generated-files/view?path=${encodeURIComponent(filePath)}`);
        const result = await response.json();
        
        if (result.error) {
            this.showNotification(`Error viewing file: ${result.error}`, 'error');
            return;
        }
        
        // Show file content in modal
        this.showFileContentModal(result.filename, result.content, result.file_type);
        
    } catch (error) {
        console.error('Error viewing file:', error);
        this.showNotification('Failed to view file', 'error');
    }
}

async downloadGeneratedFile(filePath) {
    try {
        const response = await fetch(`/api/generated-files/download?path=${encodeURIComponent(filePath)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filePath.split('/').pop();
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        this.showNotification('File downloaded successfully', 'success');
        
    } catch (error) {
        console.error('Error downloading file:', error);
        this.showNotification('Failed to download file', 'error');
    }
}

// Update the init method to include voice interface
async init() {
    console.log('Initializing dashboard...');
    
    try {
        // Setup event listeners first (these don't depend on API)
        this.setupEventListeners();
        
        // Setup conversational AI
        this.setupConversationalAI();
        
        // Initialize voice interface integration
        this.initVoiceInterface();
        
        // Check system health first
        this.addActivityItem('🔍 Performing system health check...', 'status-processing');
        await this.checkSystemHealth();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Load initial data with retries and better error handling
        this.addActivityItem('📊 Loading dashboard data...', 'status-processing');
        await this.loadInitialData();
        
        console.log('Dashboard initialized successfully');
        this.addActivityItem('🎉 Dashboard initialization complete!', 'status-online');
        
        // Announce readiness via voice if enabled
        if (window.voiceInterface && window.voiceInterface.settings.autoSpeak) {
            setTimeout(() => {
                window.voiceInterface.speak('Dashboard is ready. You can now use voice commands.');
            }, 2000);
        }
        
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        this.addActivityItem('⚠️ Dashboard started with limited functionality', 'status-error');
        this.addActivityItem('💡 Try refreshing the page or check the console for details', 'status-error');
    }
}

async loadWithRetry(loadFunction, name, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            await loadFunction();
            return;
        } catch (error) {
            console.warn(`${name} failed (attempt ${attempt}/${maxRetries}):`, error);
            if (attempt === maxRetries) {
                console.error(`${name} failed after ${maxRetries} attempts`);
            } else {
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
            }
        }
    }
}

// Add this method to the Dashboard class (around line 200-300, after other methods)

async checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        const health = await response.json();
        
        if (health.status === 'healthy') {
            this.addActivityItem('✅ System health check passed', 'status-online');
            
            // Show component status
            const components = health.components;
            let healthyComponents = 0;
            let totalComponents = Object.keys(components).length;
            
            Object.entries(components).forEach(([component, status]) => {
                if (status.includes('unavailable')) {
                    this.addActivityItem(`⚠️ ${component}: ${status}`, 'status-error');
                } else {
                    this.addActivityItem(`✅ ${component}: ${status}`, 'status-online');
                    healthyComponents++;
                }
            });
            
            // Check LLM status separately
            await this.checkLLMStatus();
            
            // Show overall health summary
            const healthPercentage = Math.round((healthyComponents / totalComponents) * 100);
            this.addActivityItem(`📊 System Health: ${healthPercentage}% (${healthyComponents}/${totalComponents} components healthy)`, 'status-online');
            
        } else {
            this.addActivityItem(`❌ System health check failed: ${health.error}`, 'status-error');
        }
        
    } catch (error) {
        this.addActivityItem('❌ Could not perform health check - API may not be running', 'status-error');
        console.error('Health check failed:', error);
    }
}

async checkLLMStatus() {
    try {
        const response = await fetch('/api/llm/status');
        const result = await response.json();
        
        if (result.llm_status && result.llm_status.active_provider) {
            const providerName = result.llm_status.active_provider_name;
            this.addActivityItem(`🤖 LLM Provider: ${providerName} (Active)`, 'status-online');
            
            // Show fallback providers
            if (result.llm_status.fallback_providers && result.llm_status.fallback_providers.length > 0) {
                this.addActivityItem(`🔄 Fallback providers available: ${result.llm_status.fallback_providers.length}`, 'status-online');
            }
        } else {
            this.addActivityItem('⚠️ No LLM provider available - AI features disabled', 'status-error');
        }
        
        // Test LLM connection
        const testResponse = await fetch('/api/llm/test-connection', { method: 'POST' });
        const testResult = await testResponse.json();
        
        if (testResult.test_result && testResult.test_result.success) {
            this.addActivityItem('✅ LLM connection test passed', 'status-online');
        } else {
            this.addActivityItem(`❌ LLM connection test failed: ${testResult.test_result?.error || 'Unknown error'}`, 'status-error');
        }
        
    } catch (error) {
        this.addActivityItem('⚠️ Could not check LLM status', 'status-error');
        console.error('LLM status check failed:', error);
    }
}
// Add this method for retry logic
async loadWithRetry(loadFunction, name, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            await loadFunction();
            console.log(`${name} loaded successfully`);
            return;
        } catch (error) {
            console.warn(`${name} failed (attempt ${attempt}/${maxRetries}):`, error);
            if (attempt === maxRetries) {
                console.error(`${name} failed after ${maxRetries} attempts`);
                this.addActivityItem(`⚠️ ${name} unavailable after ${maxRetries} attempts`, 'status-error');
            } else {
                // Wait before retry (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
            }
        }
    }
}

// Update the init method
async init() {
    console.log('Initializing dashboard...');
    
    try {
        // Setup event listeners first (these don't depend on API)
        this.setupEventListeners();
        
        // Setup conversational AI
        this.setupConversationalAI();
        
        // Check system health first
        this.addActivityItem('🔍 Performing system health check...', 'status-processing');
        await this.checkSystemHealth();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Load initial data with retries and better error handling
        this.addActivityItem('📊 Loading dashboard data...', 'status-processing');
        await this.loadInitialData();
        
        console.log('Dashboard initialized successfully');
        this.addActivityItem('🎉 Dashboard initialization complete!', 'status-online');
        
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        this.addActivityItem('⚠️ Dashboard started with limited functionality', 'status-error');
        this.addActivityItem('💡 Try refreshing the page or check the console for details', 'status-error');
    }
}
    async loadIndustryConfigs() {
        try {
            const response = await fetch('/api/industry-configs');
            const data = await response.json();
            
            if (data.industries) {
                this.industryConfigs = data.industries;
                this.updateIndustrySelect();
            }
            
        } catch (error) {
            console.error('Error loading industry configs:', error);
        }
    }

    updateIndustrySelect() {
        const select = document.getElementById('industry-select');
        
        if (this.industryConfigs) {
            select.innerHTML = this.industryConfigs.map(industry => 
                `<option value="${industry.type}">${industry.name}</option>`
            ).join('');
        }
    }

    updateStats(stats) {
    // Update main stats with fallbacks
    const elements = {
        'total-associations': stats.total_associations || 0,
        'ai-enhanced': stats.ai_enhanced || 0,
        'with-websites': stats.with_websites || 0,
        'recent-discoveries': stats.recent_discoveries || 0
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
            
            // Add helpful message if no data
            if (value === 0) {
                const parentCard = element.closest('.bg-white');
                if (parentCard && !parentCard.querySelector('.no-data-message')) {
                    const message = document.createElement('div');
                    message.className = 'no-data-message text-xs text-gray-500 mt-1';
                    message.textContent = 'Run discovery to populate data';
                    element.parentNode.appendChild(message);
                }
            }
        }
    });

    // Update additional stats if elements exist
    const additionalElements = {
        'active-workflows': stats.active_workflows || 0,
        'tasks-executed': stats.tasks_executed || 0,
        'avg-execution-time': stats.avg_execution_time ? `${stats.avg_execution_time}s` : '0s',
        'success-rate': stats.success_rate ? `${Math.round(stats.success_rate)}%` : '0%'
    };

    Object.entries(additionalElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element && value !== undefined) {
            element.textContent = value;
        }
    });
}

    updateTopAssociations(associations) {
        const container = document.getElementById('top-associations');
        
        if (!associations || associations.length === 0) {
            container.innerHTML = '<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No associations found</td></tr>';
            return;
        }

        const html = associations.map(assoc => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="font-medium text-gray-900">${assoc.name || 'Unknown'}</div>
                    <div class="text-sm text-gray-500">${assoc.region || 'Unknown region'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${assoc.official_website ? 
                        `<a href="${assoc.official_website}" target="_blank" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-external-link-alt mr-1"></i>Website
                        </a>` : 
                        '<span class="text-gray-400">No website</span>'
                    }
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${assoc.ai_enhanced ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                        ${assoc.ai_enhanced ? 'AI Enhanced' : 'Basic'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${this.formatDate(assoc.updated_at)}
                </td>
            </tr>
        `).join('');

        container.innerHTML = html;
    }

    async updateMarketIntelligence(data) {
        if (!data || data.error) {
            console.log('No market intelligence data available');
            return;
        }

        // Update market intelligence display
        const container = document.getElementById('market-intelligence-content');
        if (container && data.market_intelligence) {
            const intel = data.market_intelligence;
            
            container.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="font-semibold text-gray-900 mb-2">Market Overview</h4>
                        <p class="text-sm text-gray-600">${intel.market_overview || 'No overview available'}</p>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-900 mb-2">Key Insights</h4>
                        <ul class="text-sm text-gray-600 space-y-1">
                            ${(intel.key_insights || []).slice(0, 3).map(insight => 
                                `<li><i class="fas fa-lightbulb mr-1 text-yellow-500"></i>${insight}</li>`
                            ).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
    }

    // Discovery Methods
    async triggerDiscovery() {
        try {
            const response = await fetch('/api/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    region: 'scottish',
                    use_ai: true,
                    comprehensive: true
                })
            });

            const result = await response.json();

            if (result.status === 'started') {
                this.addActivityItem('🚀 Discovery process started', 'status-processing');
                this.showDiscoveryModal();
            } else if (result.error) {
                this.addActivityItem(`❌ Discovery error: ${result.error}`, 'status-error');
            }

        } catch (error) {
            console.error('Error triggering discovery:', error);
            this.addActivityItem('❌ Failed to start discovery', 'status-error');
        }
    }

    async triggerUniversalDiscovery() {
        try {
            const industryType = document.getElementById('industry-select').value;
            const region = document.getElementById('region-select').value;
            const limit = document.getElementById('limit-select').value;
            const customKeywords = document.getElementById('custom-keywords').value
                .split(',')
                .map(k => k.trim())
                .filter(k => k);
            
            const useAI = document.getElementById('use-ai-analysis').checked;
            const saveToDb = document.getElementById('save-to-database').checked;
            const comprehensive = document.getElementById('comprehensive-analysis').checked;
            
            const response = await fetch('/api/discover-universal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    industry_type: industryType,
                    region: region,
                    limit: limit,
                    custom_keywords: customKeywords,
                    use_ai: useAI,
                    save_to_database: saveToDb,
                    comprehensive_analysis: comprehensive
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'started') {
                this.addActivityItem(`🚀 Universal discovery started for ${result.industry} in ${result.region}`, 'status-processing');
            } else if (result.error) {
                this.addActivityItem(`❌ Discovery error: ${result.error}`, 'status-error');
            }
            
        } catch (error) {
            console.error('Error triggering universal discovery:', error);
            this.addActivityItem('❌ Failed to start universal discovery', 'status-error');
        }
    }

    showDiscoveryModal() {
        const modal = document.getElementById('discovery-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    hideDiscoveryModal() {
        const modal = document.getElementById('discovery-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    updateDiscoveryProgress(data) {
        const progressBar = document.getElementById('discovery-progress');
        const progressText = document.getElementById('discovery-progress-text');
        const currentPhase = document.getElementById('current-phase');

        if (progressBar && data.progress) {
            progressBar.style.width = `${data.progress}%`;
        }

        if (progressText) {
            progressText.textContent = data.message || 'Processing...';
        }

        if (currentPhase) {
            currentPhase.textContent = data.phase || 'discovery';
        }

        // Add to activity feed
        this.addActivityItem(`🔄 ${data.message}`, 'status-processing');
    }

    handleDiscoveryCompleted(data) {
        this.hideDiscoveryModal();
        
        const message = `✅ Discovery completed! Processed ${data.total_processed || 0} organizations` +
                       (data.ai_enhanced ? ` (${data.ai_enhanced} AI enhanced)` : '');
        
        this.addActivityItem(message, 'status-online');
        
        // Refresh data
        this.loadInitialData();
        this.loadReports();
    }

    // Industry Configuration Methods
    showIndustryInfo(industryType) {
        const industry = this.industryConfigs?.find(i => i.type === industryType);
        
        if (!industry) return;
        
        const infoPanel = document.getElementById('industry-info');
        const icon = document.getElementById('industry-icon');
        const name = document.getElementById('industry-name');
        const description = document.getElementById('industry-description');
        const sources = document.getElementById('industry-sources');
        const keywords = document.getElementById('industry-keywords');
        const fields = document.getElementById('industry-fields');
        
        // Update icon based on industry
        const iconMap = {
            'housing_associations': 'fas fa-home',
            'charities': 'fas fa-heart',
            'care_homes': 'fas fa-user-nurse',
            'schools': 'fas fa-graduation-cap',
            'healthcare': 'fas fa-hospital',
            'social_enterprises': 'fas fa-handshake',
            'cooperatives': 'fas fa-users',
            'credit_unions': 'fas fa-piggy-bank',
            'community_groups': 'fas fa-people-group',
            'environmental_orgs': 'fas fa-leaf'
        };
        
        icon.className = iconMap[industryType] || 'fas fa-building';
        name.textContent = industry.name;
        description.textContent = industry.description;
        
        // Update sources
        sources.innerHTML = industry.data_sources.map(source => 
            `<li><i class="fas fa-database mr-1"></i>${source.name} (${source.type})</li>`
        ).join('');
        
        // Update keywords
        keywords.innerHTML = industry.search_keywords.map(keyword => 
            `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">${keyword}</span>`
        ).join('');
        
        // Update fields
        fields.innerHTML = industry.output_fields.map(field => 
            `<li><i class="fas fa-check mr-1 text-green-500"></i>${field}</li>`
        ).join('');
        
        infoPanel.style.display = 'block';
    }

    previewDiscoveryConfig() {
        const industryType = document.getElementById('industry-select').value;
        const region = document.getElementById('region-select').value;
        const limit = document.getElementById('limit-select').value;
        const customKeywords = document.getElementById('custom-keywords').value;
        
        const industry = this.industryConfigs?.find(i => i.type === industryType);
        
        if (industry) {
            const preview = {
                industry: industry.name,
                region: region || 'All regions',
                limit: limit || 'No limit',
                keywords: [...industry.search_keywords, ...customKeywords.split(',').map(k => k.trim()).filter(k => k)],
                sources: industry.data_sources.length,
                expectedFields: industry.output_fields.length
            };
            
            alert(`Discovery Preview:\n\nIndustry: ${preview.industry}\nRegion: ${preview.region}\nLimit: ${preview.limit}\nKeywords: ${preview.keywords.join(', ')}\nData Sources: ${preview.sources}\nExpected Fields: ${preview.expectedFields}`);
        }
    }

    saveDiscoveryConfig() {
        const config = {
            industry_type: document.getElementById('industry-select').value,
            region: document.getElementById('region-select').value,
            limit: document.getElementById('limit-select').value,
            custom_keywords: document.getElementById('custom-keywords').value,
            use_ai_analysis: document.getElementById('use-ai-analysis').checked,
            save_to_database: document.getElementById('save-to-database').checked,
            comprehensive_analysis: document.getElementById('comprehensive-analysis').checked
        };
        
        localStorage.setItem('discoveryConfig', JSON.stringify(config));
        this.addActivityItem('💾 Discovery configuration saved', 'status-online');
    }

    loadSavedConfig() {
        const saved = localStorage.getItem('discoveryConfig');
        if (saved) {
            try {
                const config = JSON.parse(saved);
                
                const elements = {
                    'industry-select': config.industry_type || 'housing_associations',
                    'region-select': config.region || 'all',
                    'limit-select': config.limit || '',
                    'custom-keywords': config.custom_keywords || ''
                };

                Object.entries(elements).forEach(([id, value]) => {
                    const element = document.getElementById(id);
                    if (element) element.value = value;
                });

                const checkboxes = {
                    'use-ai-analysis': config.use_ai_analysis !== false,
                    'save-to-database': config.save_to_database !== false,
                    'comprehensive-analysis': config.comprehensive_analysis || false
                };

                Object.entries(checkboxes).forEach(([id, checked]) => {
                    const element = document.getElementById(id);
                    if (element) element.checked = checked;
                });
                
                // Show industry info for loaded config
                this.showIndustryInfo(config.industry_type || 'housing_associations');
                
            } catch (error) {
                console.error('Error loading saved config:', error);
            }
        }
    }

    // Reports Management
    async loadReports() {
        try {
            const response = await fetch('/api/reports');
            const reports = await response.json();
            
            this.updateReportsDisplay(reports);
            
        } catch (error) {
            console.error('Error loading reports:', error);
        }
    }

    updateReportsDisplay(reports) {
        const container = document.getElementById('reports-list');
        
        const allFiles = [
            ...(reports.data_files || []).map(f => ({...f, category: 'data'})),
            ...(reports.reports || []).map(f => ({...f, category: 'reports'})),
            ...(reports.league_tables || []).map(f => ({...f, category: 'league_tables'})),
            ...(reports.market_intelligence || []).map(f => ({...f, category: 'intelligence'})),
            ...(reports.business_insights || []).map(f => ({...f, category: 'intelligence'}))
        ];
        
        if (allFiles.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500 py-4">No reports available. Run discovery to generate reports.</div>';
            return;
        }
        
        const html = allFiles.slice(0, 10).map(file => `
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div class="flex-1">
                    <div class="font-medium text-gray-900">${file.name}</div>
                    <div class="text-sm text-gray-500">${this.formatFileSize(file.size)} • ${this.formatDate(file.modified)}</div>
                </div>
                <div class="flex space-x-2">
                    <button class="text-blue-600 hover:text-blue-800 view-report-btn" data-filename="${file.name}">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="text-green-600 hover:text-green-800 download-btn" data-filename="${file.name}">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // Add event listeners
        container.querySelectorAll('.view-report-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.viewReport(e.target.closest('button').dataset.filename);
            });
        });
        
        container.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.downloadFile(e.target.closest('button').dataset.filename);
            });
        });
    }

    async loadReportsViewer() {
        try {
            const response = await fetch('/api/reports');
            const reports = await response.json();
            
            this.updateReportsViewer(reports);
            
        } catch (error) {
            console.error('Error loading reports viewer:', error);
        }
    }

    updateReportsViewer(reports) {
        const container = document.getElementById('reports-viewer-grid');
        
        const allReports = [
            ...(reports.data_files || []).map(f => ({...f, category: 'data'})),
            ...(reports.reports || []).map(f => ({...f, category: 'reports'})),
            ...(reports.league_tables || []).map(f => ({...f, category: 'league_tables'})),
            ...(reports.market_intelligence || []).map(f => ({...f, category: 'intelligence'})),
            ...(reports.business_insights || []).map(f => ({...f, category: 'intelligence'}))
        ];
        
        if (allReports.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8 col-span-full">
                    <i class="fas fa-inbox text-2xl mb-2"></i>
                    <p>No reports available. Run discovery to generate reports.</p>
                </div>
            `;
            return;
        }
        
        const html = allReports.map(report => `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow report-card" data-category="${report.category}">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-900 mb-1">${report.name}</h4>
                        <p class="text-xs text-gray-500">${this.formatFileSize(report.size)} • ${this.formatDate(report.modified)}</p>
                    </div>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${this.getCategoryColor(report.category)}">
                        ${report.type}
                    </span>
                </div>
                
                <div class="flex space-x-2">
                    <button class="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 transition-colors view-report-btn" data-filename="${report.name}">
                        <i class="fas fa-eye mr-1"></i>View
                    </button>
                    <button class="bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700 transition-colors download-report-btn" data-filename="${report.name}">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // Add event listeners
        container.querySelectorAll('.view-report-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.viewReportInDashboard(e.target.dataset.filename);
            });
        });
        
        container.querySelectorAll('.download-report-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.downloadFile(e.target.dataset.filename);
            });
        });
    }

    async viewReport(filename) {
        try {
            const response = await fetch(`/api/view-report/${filename}`);
            const data = await response.json();
            
            if (data.error) {
                alert(`Error: ${data.error}`);
                return;
            }
            
            // Show in modal
            this.showReportModal(filename, data);
            
        } catch (error) {
            console.error('Error viewing report:', error);
            alert('Error loading report');
        }
    }

    async viewReportInDashboard(filename) {
        try {
            const response = await fetch(`/api/view-report/${filename}`);
            const data = await response.json();
            
            if (data.error) {
                alert(`Error: ${data.error}`);
                return;
            }
            
            // Show the report content section
            const contentSection = document.getElementById('report-content-section');
            const titleElement = document.getElementById('current-report-title');
            const contentDisplay = document.getElementById('report-content-display');
            
            titleElement.innerHTML = `<i class="fas fa-file-alt mr-2"></i>${filename}`;
            
            // Store current filename for download
            this.currentReportFilename = filename;
            
            if (data.type === 'json') {
                contentDisplay.innerHTML = `
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="font-semibold text-gray-900">JSON Report Content</h4>
                            <span class="text-sm text-gray-500">${Object.keys(data.content).length} top-level properties</span>
                        </div>
                        <pre class="bg-white border rounded p-4 text-sm overflow-auto max-h-80">${JSON.stringify(data.content, null, 2)}</pre>
                    </div>
                `;
            } else if (data.type === 'csv') {
                const tableHtml = `
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="font-semibold text-gray-900">CSV Report Content</h4>
                            <span class="text-sm text-gray-500">${data.rows.length} rows shown (${data.preview_limit} max)</span>
                        </div>
                        <div class="bg-white border rounded overflow-hidden">
                            <div class="overflow-x-auto max-h-80">
                                <table class="min-w-full divide-y divide-gray-200">
                                    <thead class="bg-gray-50 sticky top-0">
                                        <tr>
                                            ${data.headers.map(header => `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${header}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white divide-y divide-gray-200">
                                        ${data.rows.map(row => `
                                            <tr class="hover:bg-gray-50">
                                                ${data.headers.map(header => `<td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${row[header] || ''}</td>`).join('')}
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
                contentDisplay.innerHTML = tableHtml;
            } else if (data.type === 'html') {
                contentDisplay.innerHTML = `
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h4 class="font-semibold text-gray-900">HTML Report Content</h4>
                            <button onclick="window.open('data:text/html;charset=utf-8,' + encodeURIComponent(\`${data.content.replace(/`/g, '\\`')}\`), '_blank')" class="text-blue-600 hover:text-blue-800 text-sm">
                                <i class="fas fa-external-link-alt mr-1"></i>Open in New Tab
                            </button>
                        </div>
                        <div class="bg-white border rounded p-4 max-h-80 overflow-auto">
                            ${data.content}
                        </div>
                    </div>
                `;
            }
            
            contentSection.style.display = 'block';
            contentSection.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error viewing report:', error);
            alert('Error loading report');
        }
    }

    showReportModal(filename, data) {
        const modal = document.getElementById('report-modal');
        const title = document.getElementById('report-modal-title');
        const content = document.getElementById('report-modal-content');
        
        title.textContent = filename;
        
        if (data.type === 'json') {
            content.innerHTML = `<pre class="text-sm overflow-auto max-h-96">${JSON.stringify(data.content, null, 2)}</pre>`;
        } else if (data.type === 'csv') {
            const tableHtml = `
                <div class="overflow-x-auto max-h-96">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                ${data.headers.map(header => `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">${header}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            ${data.rows.map(row => `
                                <tr>
                                    ${data.headers.map(header => `<td class="px-4 py-2 text-sm text-gray-900">${row[header] || ''}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            content.innerHTML = tableHtml;
        } else if (data.type === 'html') {
            content.innerHTML = data.content;
        }
        
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    async downloadFile(filename) {
        try {
            const response = await fetch(`/api/download/${filename}`);
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.addActivityItem(`📥 Downloaded: ${filename}`, 'status-online');
            
        } catch (error) {
            console.error('Error downloading file:', error);
            this.addActivityItem(`❌ Download failed: ${filename}`, 'status-error');
        }
    }

    async downloadAllReports() {
        try {
            const response = await fetch('/api/download-all');
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'all_reports.zip';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.addActivityItem('📦 Downloaded all reports as ZIP', 'status-online');
            
        } catch (error) {
            console.error('Error downloading all reports:', error);
            this.addActivityItem('❌ Failed to download all reports', 'status-error');
        }
    }

    getCategoryColor(category) {
        const colors = {
            'data': 'bg-blue-100 text-blue-800',
            'reports': 'bg-green-100 text-green-800',
            'league_tables': 'bg-yellow-100 text-yellow-800',
            'intelligence': 'bg-purple-100 text-purple-800'
        };
        return colors[category] || 'bg-gray-100 text-gray-800';
    }

    filterReports(category) {
        const cards = document.querySelectorAll('.report-card');
        cards.forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // ARC Returns Management
    async loadARCReturns() {
        try {
            const response = await fetch('/api/arc-returns');
            const data = await response.json();
            
            if (data.error) {
                console.error('ARC Returns error:', data.error);
                document.getElementById('arc-associations').textContent = 'Error';
                document.getElementById('arc-filings').textContent = 'Error';
                document.getElementById('arc-updated').textContent = 'Error loading data';
                return;
            }
            
            // Update stats with Scottish Housing Regulator data
            document.getElementById('arc-associations').textContent = data.total_associations || 0;
            document.getElementById('arc-filings').textContent = data.total_data_sources || 0;
            document.getElementById('arc-updated').textContent = this.formatDate(data.last_updated);
            
            // Update table with Scottish ARC data
            const tableBody = document.getElementById('arc-table');
            
            if (!data.arc_returns || data.arc_returns.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No Scottish ARC data available</td></tr>';
                return;
            }
            
            const html = data.arc_returns.slice(0, 20).map(arc => `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="font-medium text-gray-900">${arc.name}</div>
                        <div class="text-sm text-gray-500">${arc.data_source}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${arc.registration_number || 'N/A'}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${arc.stock_units || 0} units
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="text-sm text-gray-900">${arc.satisfaction_score || 'N/A'}</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${arc.year || 'N/A'}</td>
                </tr>
            `).join('');
            
            tableBody.innerHTML = html;
            
        } catch (error) {
            console.error('Error loading ARC returns:', error);
        }
    }

    async downloadARCReturns() {
        try {
            const response = await fetch('/api/download-arc-returns');
            
            if (!response.ok) {
                throw new Error('Download failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'scottish_arc_returns.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.addActivityItem('📥 Downloaded Scottish ARC returns', 'status-online');
            
        } catch (error) {
            console.error('Error downloading ARC returns:', error);
            this.addActivityItem('❌ Failed to download ARC returns', 'status-error');
        }
    }

    // Comprehensive Insights
    async loadComprehensiveInsights() {
        try {
            const response = await fetch('/api/comprehensive-insights');
            const data = await response.json();
            
            if (data.error) {
                console.log('Comprehensive insights not available:', data.error);
                return;
            }
            
            this.updateComprehensiveInsights(data);
            
        } catch (error) {
            console.log('Comprehensive insights not available yet');
        }
    }

    updateComprehensiveInsights(data) {
        const container = document.getElementById('comprehensive-insights-content');
        if (!container) return;
        
        const insights = data.insights || {};
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="bg-blue-50 rounded-lg p-4">
                    <h4 class="font-semibold text-blue-900 mb-2">Digital Maturity</h4>
                    <p class="text-sm text-blue-700">${insights.digital_maturity || 'No data available'}</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4">
                    <h4 class="font-semibold text-green-900 mb-2">Market Opportunities</h4>
                    <p class="text-sm text-green-700">${insights.market_opportunities || 'No data available'}</p>
                </div>
                <div class="bg-purple-50 rounded-lg p-4">
                    <h4 class="font-semibold text-purple-900 mb-2">Strategic Recommendations</h4>
                    <p class="text-sm text-purple-700">${insights.strategic_recommendations || 'No data available'}</p>
                </div>
            </div>
        `;
    }

    // Conversational AI Methods
    setupConversationalAI() {
        // Send message event
        document.getElementById('send-message').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key to send
        document.getElementById('user-message').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Suggestion buttons
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('user-message').value = btn.textContent.trim();
                this.sendMessage();
            });
        });

        // Voice input (if supported)
        document.getElementById('voice-input').addEventListener('click', () => {
            this.startVoiceInput();
        });

        // Clear conversation
        document.getElementById('clear-conversation').addEventListener('click', () => {
            this.clearConversation();
        });

        // Intent modal events
        document.getElementById('close-intent-modal').addEventListener('click', () => {
            this.hideIntentModal();
        });

        document.getElementById('execute-intent').addEventListener('click', () => {
            this.executeIntent();
        });

        document.getElementById('refine-request').addEventListener('click', () => {
            this.refineRequest();
        });
    }

    async sendMessage() {
        const messageInput = document.getElementById('user-message');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addChatMessage(message, 'user');
        
        // Clear input
        messageInput.value = '';

        // Show typing indicator
        this.addTypingIndicator();

        try {
            // Send to AI for understanding
            const response = await fetch('/api/ai/understand-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: {
                        timestamp: new Date().toISOString(),
                        user_agent: navigator.userAgent
                    }
                })
            });

            const result = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator();

            if (result.error) {
                this.addChatMessage(`Sorry, I encountered an error: ${result.error}`, 'ai', 'error');
                return;
            }

            // Store current intent for later use
            this.currentIntent = result;

            // Add AI response to chat
            const aiResponse = this.formatAIResponse(result);
            this.addChatMessage(aiResponse, 'ai');

            // Show intent modal if we have good understanding
            if (result.understood_intent && result.understood_intent.confidence > 0.7) {
                this.showIntentModal(result);
            } else {
                // Ask for clarification
                this.handleClarificationNeeded(result);
            }

        } catch (error) {
            this.removeTypingIndicator();
            this.addChatMessage('Sorry, I had trouble understanding your request. Please try again.', 'ai', 'error');
            console.error('Error sending message:', error);
        }
    }

    addChatMessage(message, sender, type = 'normal') {
        const chatMessages = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3 mb-4';

        const isUser = sender === 'user';
        const isError = type === 'error';

        messageDiv.innerHTML = `
            <div class="flex-shrink-0">
                <div class="w-8 h-8 ${isUser ? 'bg-green-600' : isError ? 'bg-red-600' : 'bg-blue-600'} rounded-full flex items-center justify-center">
                    <i class="fas ${isUser ? 'fa-user' : 'fa-robot'} text-white text-sm"></i>
                </div>
            </div>
            <div class="flex-1">
                <div class="${isUser ? 'bg-green-50' : isError ? 'bg-red-50' : 'bg-blue-50'} rounded-lg p-3">
                    <div class="text-gray-800">${message}</div>
                </div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-3 mb-4';
        
        typingDiv.innerHTML = `
            <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
            </div>
            <div class="flex-1">
                <div class="bg-blue-50 rounded-lg p-3">
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    formatAIResponse(result) {
        const intent = result.understood_intent;
        const approach = result.recommended_approach;
        
        let response = `I understand you want to <strong>${intent.summary}</strong><br><br>`;
        
        response += `<strong>My Confidence:</strong> ${Math.round(intent.confidence * 100)}%<br><br>`;
        
        if (approach && approach.agents) {
            response += `<strong>I recommend using ${approach.agents.length} specialized agents:</strong><br>`;
            approach.agents.slice(0, 3).forEach((agent, index) => {
                response += `${index + 1}. ${agent.description} (${agent.estimated_time})<br>`;
            });
            
            if (approach.agents.length > 3) {
                response += `... and ${approach.agents.length - 3} more agents<br>`;
            }
        }
        
        response += `<br><strong>Estimated Time:</strong> ${approach?.total_estimated_time || 'Unknown'}<br>`;
        
        if (result.can_proceed) {
            response += `<br>✅ I have enough information to proceed. Click "Execute Analysis" to start!`;
        } else {
            response += `<br>❓ I need a bit more information to give you the best results.`;
        }
        
        return response;
    }

    showIntentModal(result) {
        const modal = document.getElementById('intent-modal');
        
        // Populate understood intent
        const intentDiv = document.getElementById('understood-intent');
        const intent = result.understood_intent;
        
        intentDiv.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <h5 class="font-semibold text-gray-900 mb-2">Intent Type</h5>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        ${intent.type}
                    </span>
                </div>
                <div>
                    <h5 class="font-semibold text-gray-900 mb-2">Confidence</h5>
                    <div class="flex items-center">
                        <div class="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                            <div class="bg-blue-600 h-2 rounded-full" style="width: ${intent.confidence * 100}%"></div>
                        </div>
                        <span class="text-sm text-gray-600">${Math.round(intent.confidence * 100)}%</span>
                    </div>
                </div>
                <div class="md:col-span-2">
                    <h5 class="font-semibold text-gray-900 mb-2">Summary</h5>
                    <p class="text-gray-700">${intent.summary}</p>
                </div>
            </div>
        `;

        // Populate clarifying questions if any
        if (result.clarifying_questions && result.clarifying_questions.length > 0) {
            const questionsSection = document.getElementById('clarifying-questions-section');
            const questionsDiv = document.getElementById('clarifying-questions');
            
            questionsDiv.innerHTML = result.clarifying_questions.map((question, index) => `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <label class="block text-sm font-medium text-gray-700 mb-2">${question}</label>
                    <input type="text" class="clarification-input w-full border border-gray-300 rounded px-3 py-2" 
                           data-question="${question}" placeholder="Your answer...">
                </div>
            `).join('');
            
            questionsSection.style.display = 'block';
        } else {
            document.getElementById('clarifying-questions-section').style.display = 'none';
        }

        // Populate recommended agents
        const agentsDiv = document.getElementById('recommended-agents');
        const agents = result.recommended_approach?.agents || [];
        
        agentsDiv.innerHTML = agents.map((agent, index) => `
            <div class="border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-2">
                    <h5 class="font-semibold text-gray-900">${agent.type}</h5>
                    <span class="text-sm text-gray-500">${agent.estimated_time}</span>
                </div>
                <p class="text-gray-700 text-sm mb-2">${agent.description}</p>
                <div class="flex items-center">
                    <div class="flex-1 bg-gray-200 rounded-full h-1 mr-2">
                        <div class="bg-green-600 h-1 rounded-full" style="width: ${agent.priority}%"></div>
                    </div>
                    <span class="text-xs text-gray-500">Priority: ${agent.priority}</span>
                </div>
            </div>
        `).join('');

        // Populate execution timeline
        const timelineDiv = document.getElementById('execution-timeline');
        const executionOrder = result.recommended_approach?.execution_order || [];
        
        timelineDiv.innerHTML = `
            <div class="flex items-center space-x-2 overflow-x-auto">
                ${executionOrder.map((agentType, index) => `
                    <div class="flex items-center space-x-2 whitespace-nowrap">
                        <div class="flex items-center space-x-1">
                            <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                            <span class="text-sm text-gray-700">${agentType}</span>
                        </div>
                        ${index < executionOrder.length - 1 ? '<i class="fas fa-arrow-right text-gray-400"></i>' : ''}
                    </div>
                `).join('')}
            </div>
            <div class="mt-3 text-sm text-gray-600">
                <strong>Total Estimated Time:</strong> ${result.recommended_approach?.total_estimated_time || 'Unknown'}
            </div>
        `;

        // Show modal
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    hideIntentModal() {
        const modal = document.getElementById('intent-modal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    async executeIntent() {
        if (!this.currentIntent) {
            alert('No intent to execute');
            return;
        }

        // Collect clarifications if any
        const clarifications = {};
        document.querySelectorAll('.clarification-input').forEach(input => {
            if (input.value.trim()) {
                clarifications[input.dataset.question] = input.value.trim();
            }
        });

        try {
            // Hide modal
            this.hideIntentModal();

            // Add execution message to chat
            this.addChatMessage('🚀 Starting analysis with your specifications. This may take a few minutes...', 'ai');

            // Execute intent
            const response = await fetch('/api/ai/execute-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    intent: this.currentIntent.understood_intent,
                    recommendations: this.currentIntent.recommended_approach.agents,
                    execution_order: this.currentIntent.recommended_approach.execution_order,
                    confirmations: clarifications
                })
            });

            const result = await response.json();

            if (result.error) {
                this.addChatMessage(`❌ Error starting analysis: ${result.error}`, 'ai', 'error');
            } else {
                this.addChatMessage(`✅ Analysis started! I'm now executing ${result.agents_count} specialized agents. You'll see real-time updates below.`, 'ai');
                
                // Add to activity feed
                this.addActivityItem(`🤖 AI-driven analysis started (${result.agents_count} agents)`, 'status-processing');
            }

        } catch (error) {
            console.error('Error executing intent:', error);
            this.addChatMessage('❌ Failed to start analysis. Please try again.', 'ai', 'error');
        }
    }

    refineRequest() {
        this.hideIntentModal();
        
        // Focus on input for refinement
        const messageInput = document.getElementById('user-message');
        messageInput.focus();
        
        this.addChatMessage('Please refine your request with more specific details.', 'ai');
    }

    clearConversation() {
        const chatMessages = document.getElementById('chat-messages');
        
        // Keep only the initial AI greeting
        chatMessages.innerHTML = `
            <div class="flex items-start space-x-3 mb-4">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                        <i class="fas fa-robot text-white text-sm"></i>
                    </div>
                </div>
                <div class="flex-1">
                    <div class="bg-blue-50 rounded-lg p-3">
                        <p class="text-gray-800">
                            👋 Hi! I'm your AI assistant. Tell me what you're looking for and I'll help you discover and analyze organizations.
                        </p>
                    </div>
                </div>
            </div>
        `;
        
        this.currentIntent = null;
    }

    startVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('Voice input is not supported in your browser');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        const voiceBtn = document.getElementById('voice-input');
        const originalHTML = voiceBtn.innerHTML;
        
        voiceBtn.innerHTML = '<i class="fas fa-stop text-red-500"></i>';
        voiceBtn.disabled = true;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('user-message').value = transcript;
            
            voiceBtn.innerHTML = originalHTML;
            voiceBtn.disabled = false;
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            voiceBtn.innerHTML = originalHTML;
            voiceBtn.disabled = false;
        };

        recognition.onend = () => {
            voiceBtn.innerHTML = originalHTML;
            voiceBtn.disabled = false;
        };

        recognition.start();
    }

    handleClarificationNeeded(result) {
        if (result.clarifying_questions && result.clarifying_questions.length > 0) {
            const questions = result.clarifying_questions.slice(0, 3).join('<br>• ');
            this.addChatMessage(`I need a bit more information to help you better:<br><br>• ${questions}<br><br>Please provide more details or click "Execute Analysis" if you'd like to proceed with what I understand so far.`, 'ai');
        }
    }

    handleIntentExecutionUpdate(data) {
        if (data.type === 'intent_execution_started') {
            this.addChatMessage(`🔄 Analysis pipeline started with ${data.agents_count} agents`, 'ai');
        } else if (data.type === 'intent_execution_completed') {
            const results = data.results;
            const summary = results.pipeline_summary;
            
            this.addChatMessage(`✅ Analysis completed! Executed ${summary.executed_agents} agents with ${summary.successful_agents} successful. Results are now available in the reports section.`, 'ai');
            
            // Refresh reports and data
            this.loadReports();
            this.loadReportsViewer();
            this.loadInitialData();
            
        } else if (data.type === 'intent_execution_failed') {
            this.addChatMessage(`❌ Analysis failed: ${data.error}`, 'ai', 'error');
        }
    }

    // Activity Feed Management
    addActivityItem(message, status) {
        const activityFeed = document.getElementById('activity-feed');
        if (!activityFeed) return;
        
        const activityItem = document.createElement('div');
        activityItem.className = `activity-item ${status} flex items-center space-x-3 p-3 border-l-4 mb-2`;
        
        const statusColors = {
            'status-online': 'border-green-500 bg-green-50',
            'status-processing': 'border-blue-500 bg-blue-50',
            'status-offline': 'border-gray-500 bg-gray-50',
            'status-error': 'border-red-500 bg-red-50'
        };
        
        activityItem.className += ` ${statusColors[status] || 'border-gray-500 bg-gray-50'}`;
        
        activityItem.innerHTML = `
            <div class="flex-1">
                <p class="text-sm text-gray-800">${message}</p>
                <p class="text-xs text-gray-500">${this.formatDate(new Date())}</p>
            </div>
        `;
        
        // Add to top of feed
        activityFeed.insertBefore(activityItem, activityFeed.firstChild);
        
        // Keep only last 50 items
        while (activityFeed.children.length > 50) {
            activityFeed.removeChild(activityFeed.lastChild);
        }
    }

    // Utility Methods
    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } catch (error) {
            return 'Invalid date';
        }
    }

    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    // Event Listeners Setup
    setupEventListeners() {
        // Discovery buttons
        document.getElementById('discover-btn').addEventListener('click', () => {
            this.triggerDiscovery();
        });
        
        document.getElementById('discover-btn-enhanced').addEventListener('click', () => {
            this.triggerUniversalDiscovery();
        });

        // Modal close buttons
        document.getElementById('close-modal').addEventListener('click', () => {
            this.hideDiscoveryModal();
        });

        document.getElementById('close-report-modal').addEventListener('click', () => {
            document.getElementById('report-modal').classList.add('hidden');
            document.getElementById('report-modal').classList.remove('flex');
        });

        // Reports management
        document.getElementById('refresh-reports').addEventListener('click', () => {
            this.loadReports();
        });

        document.getElementById('refresh-reports-viewer').addEventListener('click', () => {
            this.loadReportsViewer();
        });

        document.getElementById('download-all').addEventListener('click', () => {
            this.downloadAllReports();
        });

        document.getElementById('download-arc').addEventListener('click', () => {
            this.downloadARCReturns();
        });

        // Report viewer controls
        document.getElementById('report-filter').addEventListener('change', (e) => {
            this.filterReports(e.target.value);
        });

        document.getElementById('close-report-viewer').addEventListener('click', () => {
            document.getElementById('report-content-section').style.display = 'none';
        });

        document.getElementById('download-current-report').addEventListener('click', () => {
            if (this.currentReportFilename) {
                this.downloadFile(this.currentReportFilename);
            }
        });

        // Industry configuration
        document.getElementById('industry-select').addEventListener('change', (e) => {
            this.showIndustryInfo(e.target.value);
        });

        document.getElementById('preview-config').addEventListener('click', () => {
            this.previewDiscoveryConfig();
        });

        document.getElementById('save-config').addEventListener('click', () => {
            this.saveDiscoveryConfig();
        });

        // Conversation history
        document.getElementById('conversation-history').addEventListener('click', () => {
            this.showConversationHistory();
        });
    }

    async showConversationHistory() {
        try {
            const response = await fetch('/api/ai/conversation-history');
            const data = await response.json();
            
            if (data.conversation_history) {
                const historyText = data.conversation_history.map(msg => 
                    `[${this.formatDate(msg.timestamp)}] User: ${msg.user_message}`
                ).join('\n\n');
                
                alert(`Conversation History (${data.total_messages} total messages):\n\n${historyText}`);
            }
            
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});