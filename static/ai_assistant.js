/**
 * Gemini AI Assistant Component
 * Handles the chat interface and communication with the /ai/chat endpoints.
 */
class AIAssistant {
    constructor() {
        this.container = null;
        this.chatWindow = null;
        this.messagesContainer = null;
        this.inputField = null;
        this.isOpen = false;
        this.role = document.body.dataset.role || 'student'; // Set in template
        
        this.init();
    }

    init() {
        this.createElements();
        this.addEventListeners();
    }

    createElements() {
        this.container = document.createElement('div');
        this.container.className = 'ai-assistant-container';
        
        this.container.innerHTML = `
            <button class="ai-toggle-btn" title="AI Assistant">
                <i class="fas fa-comment-dots"></i>
            </button>
            <div class="ai-chat-window">
                <div class="ai-chat-header">
                    <div class="ai-chat-header-info">
                        <div class="ai-status-dot"></div>
                        <h3>Campus AI</h3>
                    </div>
                    <i class="fas fa-robot" style="opacity: 0.5;"></i>
                </div>
                <div class="ai-chat-messages" id="ai-chat-messages">
                    <div class="message ai">
                        Hello! I'm your Smart Campus AI. How can I help you today?
                    </div>
                </div>
                <div class="ai-chat-input">
                    <input type="text" placeholder="Type your message..." id="ai-chat-input">
                    <button id="ai-send-btn">
                        <i class="fas fa-arrow-up"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.container);
        
        this.chatWindow = this.container.querySelector('.ai-chat-window');
        this.messagesContainer = this.container.querySelector('.ai-chat-messages');
        this.inputField = this.container.querySelector('#ai-chat-input');
    }

    addEventListeners() {
        const toggleBtn = this.container.querySelector('.ai-toggle-btn');
        const sendBtn = this.container.querySelector('#ai-send-btn');

        toggleBtn.addEventListener('click', () => this.toggleChat());
        
        sendBtn.addEventListener('click', () => this.handleSendMessage());
        
        this.inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSendMessage();
        });
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        this.chatWindow.classList.toggle('active', this.isOpen);
        if (this.isOpen) {
            this.inputField.focus();
            const icon = this.container.querySelector('.ai-toggle-btn i');
            icon.className = this.isOpen ? 'fas fa-times' : 'fas fa-comment-dots';
        } else {
            const icon = this.container.querySelector('.ai-toggle-btn i');
            icon.className = 'fas fa-comment-dots';
        }
    }

    async handleSendMessage() {
        const message = this.inputField.value.trim();
        if (!message || this.isThinking) return;

        this.isThinking = true;
        this.addMessage(message, 'user');
        this.inputField.value = '';
        this.inputField.disabled = true;
        
        const loadingMsg = this.showTypingIndicator();
        
        try {
            const endpoint = this.role === 'faculty' ? '/ai/chat/faculty' : '/ai/chat/student';
            const body = this.role === 'faculty' ? { query: message } : { message: message };

            const data = await fetchAuth(endpoint, {
                method: 'POST',
                body: JSON.stringify(body)
            });
            
            loadingMsg.remove();
            
            if (data.error) {
                this.addMessage(`Error: ${data.error}`, 'ai');
            } else {
                this.addMessage(data.response, 'ai');
            }
        } catch (error) {
            loadingMsg.remove();
            this.addMessage("Sorry, I'm having trouble connecting right now.", 'ai');
            console.error("AI Chat Error:", error);
        } finally {
            this.isThinking = false;
            this.inputField.disabled = false;
            this.inputField.focus();
        }
        
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message ai';
        div.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        this.messagesContainer.appendChild(div);
        this.scrollToBottom();
        return div;
    }

    addMessage(text, side) {
        const div = document.createElement('div');
        div.className = `message ${side}`;
        // Support simple multiline
        div.innerHTML = text.replace(/\n/g, '<br>');
        this.messagesContainer.appendChild(div);
        this.scrollToBottom();
        return div;
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aiAssistant = new AIAssistant();
});
