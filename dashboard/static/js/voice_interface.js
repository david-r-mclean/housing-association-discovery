/**
 * Advanced Voice Interface for Dashboard
 * Provides ChatGPT-like voice input/output capabilities
 */

class VoiceInterface {
    constructor() {
        this.isListening = false;
        this.isSpeaking = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.voices = [];
        this.currentVoice = null;
        this.audioContext = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        // Voice settings
        this.settings = {
            language: 'en-US',
            voiceSpeed: 1.0,
            voicePitch: 1.0,
            voiceVolume: 1.0,
            autoSpeak: true,
            wakeWord: 'hey dashboard',
            continuousListening: false,
            noiseReduction: true
        };
        
        this.init();
    }
    
    async init() {
        console.log('Initializing Voice Interface...');
        
        // Initialize speech recognition
        this.initSpeechRecognition();
        
        // Initialize speech synthesis
        this.initSpeechSynthesis();
        
        // Initialize audio context for advanced features
        await this.initAudioContext();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load user preferences
        this.loadSettings();
        
        console.log('Voice Interface initialized successfully');
    }
    
    initSpeechRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported');
            this.showVoiceError('Speech recognition is not supported in your browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure recognition
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = this.settings.language;
        this.recognition.maxAlternatives = 3;
        
        // Event handlers
        this.recognition.onstart = () => {
            console.log('Speech recognition started');
            this.isListening = true;
            this.updateVoiceUI('listening');
            this.showVoiceStatus('Listening...', 'listening');
        };
        
        this.recognition.onresult = (event) => {
            this.handleSpeechResult(event);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateVoiceUI('idle');
            this.handleSpeechError(event.error);
        };
        
        this.recognition.onend = () => {
            console.log('Speech recognition ended');
            this.isListening = false;
            this.updateVoiceUI('idle');
            
            // Restart if continuous listening is enabled
            if (this.settings.continuousListening && !this.isSpeaking) {
                setTimeout(() => this.startListening(), 1000);
            }
        };
    }
    
    initSpeechSynthesis() {
        if (!this.synthesis) {
            console.warn('Speech synthesis not supported');
            return;
        }
        
        // Load available voices
        this.loadVoices();
        
        // Handle voice changes
        this.synthesis.onvoiceschanged = () => {
            this.loadVoices();
        };
    }
    
    async initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio context initialized');
        } catch (error) {
            console.warn('Could not initialize audio context:', error);
        }
    }
    
    loadVoices() {
        this.voices = this.synthesis.getVoices();
        
        // Find a good default voice
        this.currentVoice = this.voices.find(voice => 
            voice.lang.startsWith(this.settings.language.split('-')[0]) && 
            voice.name.includes('Neural')
        ) || this.voices.find(voice => 
            voice.lang.startsWith(this.settings.language.split('-')[0])
        ) || this.voices[0];
        
        // Update voice selector UI
        this.updateVoiceSelector();
        
        console.log(`Loaded ${this.voices.length} voices, selected: ${this.currentVoice?.name}`);
    }
    
    setupEventListeners() {
        // Voice control buttons
        document.getElementById('start-voice-input')?.addEventListener('click', () => {
            this.toggleListening();
        });
        
        document.getElementById('stop-voice-input')?.addEventListener('click', () => {
            this.stopListening();
        });
        
        document.getElementById('toggle-continuous-listening')?.addEventListener('click', () => {
            this.toggleContinuousListening();
        });
        
        // Voice settings
        document.getElementById('voice-speed')?.addEventListener('input', (e) => {
            this.settings.voiceSpeed = parseFloat(e.target.value);
            this.saveSettings();
        });
        
        document.getElementById('voice-pitch')?.addEventListener('input', (e) => {
            this.settings.voicePitch = parseFloat(e.target.value);
            this.saveSettings();
        });
        
        document.getElementById('voice-volume')?.addEventListener('input', (e) => {
            this.settings.voiceVolume = parseFloat(e.target.value);
            this.saveSettings();
        });
        
        document.getElementById('voice-selector')?.addEventListener('change', (e) => {
            const selectedVoice = this.voices.find(voice => voice.name === e.target.value);
            if (selectedVoice) {
                this.currentVoice = selectedVoice;
                this.saveSettings();
            }
        });
        
        // Auto-speak toggle
        document.getElementById('auto-speak-toggle')?.addEventListener('change', (e) => {
            this.settings.autoSpeak = e.target.checked;
            this.saveSettings();
        });
        
        // Wake word settings
        document.getElementById('wake-word-input')?.addEventListener('change', (e) => {
            this.settings.wakeWord = e.target.value.toLowerCase();
            this.saveSettings();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + V to toggle voice input
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                this.toggleListening();
            }
            
            // Escape to stop listening/speaking
            if (e.key === 'Escape') {
                this.stopListening();
                this.stopSpeaking();
            }
        });
    }
    
    handleSpeechResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update UI with interim results
        if (interimTranscript) {
            this.showInterimTranscript(interimTranscript);
        }
        
        // Process final transcript
        if (finalTranscript) {
            this.processFinalTranscript(finalTranscript.trim());
        }
    }
    
    processFinalTranscript(transcript) {
        console.log('Final transcript:', transcript);
        
        // Check for wake word if continuous listening is enabled
        if (this.settings.continuousListening && this.settings.wakeWord) {
            if (!transcript.toLowerCase().includes(this.settings.wakeWord)) {
                return; // Ignore if wake word not detected
            }
            
            // Remove wake word from transcript
            transcript = transcript.toLowerCase().replace(this.settings.wakeWord, '').trim();
        }
        
        // Check for voice commands
        if (this.handleVoiceCommands(transcript)) {
            return; // Command was handled
        }
        
        // Send to dashboard AI
        this.sendVoiceMessageToDashboard(transcript);
    }
    
    handleVoiceCommands(transcript) {
        const lowerTranscript = transcript.toLowerCase();
        
        // Voice control commands
        if (lowerTranscript.includes('stop listening')) {
            this.stopListening();
            this.speak('Voice input stopped');
            return true;
        }
        
        if (lowerTranscript.includes('start listening')) {
            this.startListening();
            this.speak('Voice input started');
            return true;
        }
        
        if (lowerTranscript.includes('clear conversation')) {
            if (window.dashboard) {
                window.dashboard.clearConversation();
                this.speak('Conversation cleared');
            }
            return true;
        }
        
        if (lowerTranscript.includes('refresh dashboard')) {
            if (window.dashboard) {
                window.dashboard.loadInitialData();
                this.speak('Dashboard refreshed');
            }
            return true;
        }
        
        if (lowerTranscript.includes('show help')) {
            this.showVoiceHelp();
            return true;
        }
        
        // Settings commands
        if (lowerTranscript.includes('speak slower')) {
            this.settings.voiceSpeed = Math.max(0.5, this.settings.voiceSpeed - 0.2);
            this.saveSettings();
            this.speak('Speaking slower now');
            return true;
        }
        
        if (lowerTranscript.includes('speak faster')) {
            this.settings.voiceSpeed = Math.min(2.0, this.settings.voiceSpeed + 0.2);
            this.saveSettings();
            this.speak('Speaking faster now');
            return true;
        }
        
        return false; // No command matched
    }
    
    async sendVoiceMessageToDashboard(transcript) {
        try {
            this.showVoiceStatus('Processing...', 'processing');
            
            // Add voice message to chat
            if (window.dashboard && window.dashboard.addChatMessage) {
                window.dashboard.addChatMessage(transcript, 'user');
            }
            
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
                        voice_settings: this.settings
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.error) {
                this.showVoiceError(`Error: ${result.error}`);
                if (window.dashboard && window.dashboard.addChatMessage) {
                    window.dashboard.addChatMessage(`Error: ${result.error}`, 'ai', 'error');
                }
                return;
            }
            
            // Add AI response to chat
            if (window.dashboard && window.dashboard.addChatMessage) {
                window.dashboard.addChatMessage(result.message, 'ai');
            }
            
            // Speak response if auto-speak is enabled
            if (this.settings.autoSpeak && result.voice_response) {
                this.speak(result.voice_response);
            } else if (this.settings.autoSpeak && result.message) {
                // Use main message if no voice-specific response
                this.speak(this.extractTextFromHTML(result.message));
            }
            
            this.showVoiceStatus('Ready', 'ready');
            
        } catch (error) {
            console.error('Error sending voice message:', error);
            this.showVoiceError('Failed to process voice message');
        }
    }
    
    speak(text, options = {}) {
        if (!this.synthesis || !text) return;
        
        // Stop any current speech
        this.synthesis.cancel();
        
        // Clean text for speech
        const cleanText = this.extractTextFromHTML(text);
        
        if (!cleanText.trim()) return;
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Configure utterance
        utterance.voice = this.currentVoice;
        utterance.rate = options.rate || this.settings.voiceSpeed;
        utterance.pitch = options.pitch || this.settings.voicePitch;
        utterance.volume = options.volume || this.settings.voiceVolume;
        
        // Event handlers
        utterance.onstart = () => {
            this.isSpeaking = true;
            this.updateVoiceUI('speaking');
            this.showVoiceStatus('Speaking...', 'speaking');
        };
        
        utterance.onend = () => {
            this.isSpeaking = false;
            this.updateVoiceUI('idle');
            this.showVoiceStatus('Ready', 'ready');
            
            // Resume listening if continuous mode is enabled
            if (this.settings.continuousListening && !this.isListening) {
                setTimeout(() => this.startListening(), 500);
            }
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
            this.isSpeaking = false;
            this.updateVoiceUI('idle');
            this.showVoiceError('Speech synthesis error');
        };
        
        // Speak
        this.synthesis.speak(utterance);
    }
    
    startListening() {
        if (!this.recognition || this.isListening) return;
        
        try {
            // Stop any current speech
            this.stopSpeaking();
            
            this.recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.showVoiceError('Could not start voice input');
        }
    }
    
    stopListening() {
        if (!this.recognition || !this.isListening) return;
        
        try {
            this.recognition.stop();
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }
    
    stopSpeaking() {
        if (!this.synthesis || !this.isSpeaking) return;
        
        this.synthesis.cancel();
        this.isSpeaking = false;
        this.updateVoiceUI('idle');
    }
    
    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }
    
    toggleContinuousListening() {
        this.settings.continuousListening = !this.settings.continuousListening;
        this.saveSettings();
        
        if (this.settings.continuousListening) {
            this.speak('Continuous listening enabled');
            this.startListening();
        } else {
            this.speak('Continuous listening disabled');
            this.stopListening();
        }
        
        this.updateContinuousListeningUI();
    }
    
    // UI Update Methods
    updateVoiceUI(state) {
        const voiceButton = document.getElementById('voice-control-button');
        const voiceIndicator = document.getElementById('voice-indicator');
        
        if (voiceButton) {
            voiceButton.className = `voice-control-button ${state}`;
            
            switch (state) {
                case 'listening':
                    voiceButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                    voiceButton.title = 'Stop Listening';
                    break;
                case 'speaking':
                    voiceButton.innerHTML = '<i class="fas fa-volume-up"></i>';
                    voiceButton.title = 'Speaking...';
                    break;
                case 'processing':
                    voiceButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                    voiceButton.title = 'Processing...';
                    break;
                default:
                    voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
                    voiceButton.title = 'Start Voice Input';
            }
        }
        
        if (voiceIndicator) {
            voiceIndicator.className = `voice-indicator ${state}`;
        }
    }
    
    showVoiceStatus(message, type = 'info') {
        const statusElement = document.getElementById('voice-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `voice-status ${type}`;
            
            // Auto-hide after 3 seconds for non-persistent states
            if (type !== 'listening' && type !== 'speaking') {
                setTimeout(() => {
                    if (statusElement.textContent === message) {
                        statusElement.textContent = 'Ready';
                        statusElement.className = 'voice-status ready';
                    }
                }, 3000);
            }
        }
    }
    
    showInterimTranscript(transcript) {
        const interimElement = document.getElementById('interim-transcript');
        if (interimElement) {
            interimElement.textContent = transcript;
            interimElement.style.display = 'block';
        }
    }
    
    showVoiceError(message) {
        this.showVoiceStatus(message, 'error');
        console.error('Voice Interface Error:', message);
        
        // Show notification
        if (window.dashboard && window.dashboard.showNotification) {
            window.dashboard.showNotification(message, 'error');
        }
    }
    
    updateVoiceSelector() {
        const selector = document.getElementById('voice-selector');
        if (!selector || !this.voices.length) return;
        
        selector.innerHTML = this.voices.map(voice => 
            `<option value="${voice.name}" ${voice === this.currentVoice ? 'selected' : ''}>
                ${voice.name} (${voice.lang})
            </option>`
        ).join('');
    }
    
    updateContinuousListeningUI() {
        const toggle = document.getElementById('continuous-listening-toggle');
        if (toggle) {
            toggle.checked = this.settings.continuousListening;
        }
        
        const indicator = document.getElementById('continuous-listening-indicator');
        if (indicator) {
            indicator.style.display = this.settings.continuousListening ? 'block' : 'none';
        }
    }
    
    showVoiceHelp() {
        const helpText = `
        Voice Commands Available:
        
        • "Hey Dashboard" - Wake word for continuous listening
        • "Stop listening" - Stop voice input
        • "Start listening" - Start voice input
        • "Clear conversation" - Clear chat history
        • "Refresh dashboard" - Reload dashboard data
        • "Speak slower/faster" - Adjust speech speed
        • "Show help" - Display this help
        
        You can also ask natural questions like:
        • "Find housing associations in Scotland"
        • "Create a new dashboard component"
        • "Analyze regulatory documents"
        • "Generate a compliance report"
        
        Keyboard Shortcuts:
        • Ctrl/Cmd + Shift + V - Toggle voice input
        • Escape - Stop listening/speaking
        `;
        
        this.speak('Here are the available voice commands');
        
        if (window.dashboard && window.dashboard.addChatMessage) {
            window.dashboard.addChatMessage(helpText, 'ai');
        }
    }
    
    // Utility Methods
    extractTextFromHTML(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }
    
    handleSpeechError(error) {
        let message = 'Voice input error';
        
        switch (error) {
            case 'no-speech':
                message = 'No speech detected. Please try again.';
                break;
            case 'audio-capture':
                message = 'Microphone not accessible. Please check permissions.';
                break;
            case 'not-allowed':
                message = 'Microphone permission denied. Please enable microphone access.';
                break;
            case 'network':
                message = 'Network error. Please check your connection.';
                break;
            case 'aborted':
                message = 'Voice input was cancelled.';
                break;
            default:
                message = `Voice input error: ${error}`;
        }
        
        this.showVoiceError(message);
    }
    
    // Settings Management
    saveSettings() {
        localStorage.setItem('voiceInterfaceSettings', JSON.stringify({
            ...this.settings,
            currentVoiceName: this.currentVoice?.name
        }));
    }
    
    loadSettings() {
        try {
            const saved = localStorage.getItem('voiceInterfaceSettings');
            if (saved) {
                const settings = JSON.parse(saved);
                this.settings = { ...this.settings, ...settings };
                
                // Restore voice selection
                if (settings.currentVoiceName) {
                    const voice = this.voices.find(v => v.name === settings.currentVoiceName);
                    if (voice) {
                        this.currentVoice = voice;
                    }
                }
                
                this.updateSettingsUI();
            }
        } catch (error) {
            console.error('Error loading voice settings:', error);
        }
    }
    
    updateSettingsUI() {
        // Update UI elements with current settings
        const elements = {
            'voice-speed': this.settings.voiceSpeed,
            'voice-pitch': this.settings.voicePitch,
            'voice-volume': this.settings.voiceVolume,
            'wake-word-input': this.settings.wakeWord,
            'auto-speak-toggle': this.settings.autoSpeak,
            'continuous-listening-toggle': this.settings.continuousListening
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = value;
                } else {
                    element.value = value;
                }
            }
        });
    }
    
    // Public API
    isVoiceSupported() {
        return !!(this.recognition && this.synthesis);
    }
    
    getVoiceCapabilities() {
        return {
            speechRecognition: !!this.recognition,
            speechSynthesis: !!this.synthesis,
            audioContext: !!this.audioContext,
            voiceCount: this.voices.length,
            currentVoice: this.currentVoice?.name,
            isListening: this.isListening,
            isSpeaking: this.isSpeaking,
            continuousListening: this.settings.continuousListening
        };
    }
}

// Initialize voice interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.voiceInterface = new VoiceInterface();
});

// Export for global access
window.VoiceInterface = VoiceInterface;