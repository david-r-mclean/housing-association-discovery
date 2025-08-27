/**
 * Dashboard JavaScript - Clean Implementation
 */

console.log('Dashboard.js loaded');

// Simple Dashboard class
class Dashboard {
    constructor() {
        console.log('Dashboard constructor called');
        this.init();
    }

    init() {
        console.log('Dashboard initializing...');
        try {
            this.setupEventListeners();
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
        }
    }

    setupEventListeners() {
        // Setup chat input - check if element exists first
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage(); // Use global function
                }
            });
            console.log('Chat input listener added');
        } else {
            console.warn('Chat input element not found');
        }

        // Setup voice toggle - check if element exists first
        const voiceToggle = document.getElementById('voiceToggle');
        if (voiceToggle) {
            voiceToggle.addEventListener('click', () => {
                this.toggleVoice();
            });
            console.log('Voice toggle listener added');
        } else {
            console.warn('Voice toggle element not found');
        }
    }

    toggleVoice() {
        if (window.voiceInterface) {
            window.voiceInterface.toggleListening();
        } else {
            console.warn('Voice interface not available');
        }
    }
}

// Make Dashboard available globally
window.Dashboard = Dashboard;