class ChatApp {
    constructor() {
        // Configuration - Update these URLs to match your FastAPI server
        this.API_BASE_URL = '{{API_BASE_URL}}';
        
        // Conversation history
        this.conversationHistory = [];
        
        // Theme state (default to dark)
        this.currentTheme = 'dark';
        
        // DOM elements
        this.messagesContainer = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.clearHistoryBtn = document.getElementById('clearHistoryBtn');
        this.historyIndicator = document.getElementById('historyIndicator');
        this.themeSelector = document.getElementById('themeSelector');
        
        this.initializeEventListeners();
        this.updateHistoryIndicator();
        this.loadTheme();
    }

    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        this.themeSelector.addEventListener('change', (e) => this.changeTheme(e.target.value));
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    changeTheme(theme) {
        this.currentTheme = theme;
        document.body.className = theme;
        this.themeSelector.value = theme;
        this.saveTheme();
    }

    saveTheme() {
        // Store theme preference in memory (since localStorage isn't available)
        window.currentTheme = this.currentTheme;
    }

    loadTheme() {
        // Load theme from memory if available, otherwise use dark as default
        if (window.currentTheme) {
            this.currentTheme = window.currentTheme;
        } else {
            this.currentTheme = 'dark';
        }
        document.body.className = this.currentTheme;
        this.themeSelector.value = this.currentTheme;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to chat UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.setInputEnabled(false);
        this.showTypingIndicator();

        try {
            const response = await this.callAgentAPI(message);
            this.hideTypingIndicator();
            this.addMessage(response.response, 'assistant');
            
            // Update conversation history from server response
            if (response.history) {
                this.conversationHistory = response.history;
                this.updateHistoryIndicator();
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addErrorMessage('Sorry, I encountered an error: ' + error.message);
        } finally {
            this.setInputEnabled(true);
            this.messageInput.focus();
        }
    }

    async callAgentAPI(message) {
        const response = await fetch(`${this.API_BASE_URL}/agent/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'depends': '{{DEPENDS}}',
            },
            body: JSON.stringify({
                query: message,
                history: this.conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(content)}
            </div>
        `;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addErrorMessage(content) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = content;
        this.messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Basic formatting - convert line breaks and make links clickable
        return content
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    setInputEnabled(enabled) {
        this.messageInput.disabled = !enabled;
        this.sendButton.disabled = !enabled;
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    clearHistory() {
        // Clear conversation history
        this.conversationHistory = [];
        
        // Clear chat messages (keep initial greeting)
        const initialMessage = this.messagesContainer.querySelector('.message.assistant');
        this.messagesContainer.innerHTML = '';
        if (initialMessage) {
            this.messagesContainer.appendChild(initialMessage.cloneNode(true));
        }
        
        // Update history indicator
        this.updateHistoryIndicator();
        
        // Show confirmation
        this.addMessage('✨ Conversation history cleared! Starting fresh.', 'assistant');
    }

    updateHistoryIndicator() {
        const messageCount = this.conversationHistory.length;
        this.historyIndicator.textContent = `History: ${messageCount} messages`;
    }
}

// Initialize the chat app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});