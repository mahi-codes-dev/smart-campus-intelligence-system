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
                <i class="fas fa-robot"></i>
            </button>
            <div class="ai-chat-window">
                <div class="ai-chat-header">
                    <i class="fas fa-brain"></i>
                    <h3>Campus AI Assistant</h3>
                </div>
                <div class="ai-chat-messages" id="ai-chat-messages">
                    <div class="message ai">
                        Hello! I'm your Smart Campus AI. How can I help you today?
                    </div>
                </div>
                <div class="ai-chat-input">
                    <input type="text" placeholder="Ask me anything..." id="ai-chat-input">
                    <button id="ai-send-btn">
                        <i class="fas fa-paper-plane"></i>
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
        }
    }

    async handleSendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.inputField.value = '';
        
        const loadingMsg = this.addMessage('Thinking...', 'ai');
        
        try {
            const endpoint = this.role === 'faculty' ? '/ai/chat/faculty' : '/ai/chat/student';
            const body = this.role === 'faculty' ? { query: message } : { message: message };

            const data = await fetchAuth(endpoint, {
                method: 'POST',
                body: JSON.stringify(body)
            });
            
            if (data.error) {
                loadingMsg.textContent = `Error: ${data.error}`;
            } else {
                loadingMsg.textContent = data.response;
            }
        } catch (error) {
            loadingMsg.textContent = "Sorry, I'm having trouble connecting right now.";
            console.error("AI Chat Error:", error);
        }
        
        this.scrollToBottom();
    }

    addMessage(text, side) {
        const div = document.createElement('div');
        div.className = `message ${side}`;
        div.textContent = text;
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
