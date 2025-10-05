document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Allow sending message with the Enter key
    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
});

/**
 * Creates and appends a new message bubble to the chat window.
 * @param {string} content - The message text.
 * @param {string} sender - 'user' or 'assistant'.
 */
function appendMessage(content, sender) {
    const chatMessages = document.getElementById('chat-messages');
    
    // Sanitize content before injecting into DOM (XSS protection)
    const sanitizedContent = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.innerHTML = sanitizedContent.replace(/\n/g, '<br>'); // Handle newlines
    
    const metaDiv = document.createElement('div');
    metaDiv.classList.add('message-meta');
    metaDiv.textContent = sender === 'user' ? 'You' : 'AI Assistant';

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(metaDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to the bottom for a seamless experience
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Handles the sending of a message to the Flask backend.
 */
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();

    if (!message) return;

    // Show user message immediately
    appendMessage(message, 'user');
    
    // Clear input and disable UI during processing
    input.value = '';
    toggleUI(false); 

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        // Render AI response or error message
        appendMessage(data.response, 'assistant');

    } catch (error) {
        console.error('Fetch error:', error);
        appendMessage("Network error: Could not connect to the server.", 'assistant');
    } finally {
        // Re-enable UI and focus input
        toggleUI(true); 
    }
}

/**
 * Toggles the state of the UI elements (input, button, spinner).
 * @param {boolean} enable - True to enable, false to disable/show loading.
 */
function toggleUI(enable) {
    const input = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const spinner = document.getElementById('loading-spinner');

    input.disabled = !enable;
    sendButton.disabled = !enable;
    spinner.style.display = enable ? 'none' : 'flex';
    
    if (enable) {
        input.focus();
    }
}