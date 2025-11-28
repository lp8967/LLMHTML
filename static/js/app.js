document.getElementById('topKSlider').addEventListener('input', function() {
    document.getElementById('topKValue').textContent = this.value;
});

async function sendQuestion() {
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value.trim();
    
    if (!question) return;

    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    try {
        addMessageToChat('user', question);
        questionInput.value = '';
        showTypingIndicator();

        const strategy = document.getElementById('strategySelect').value;
        const topK = document.getElementById('topKSlider').value;

        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                top_k: parseInt(topK),
                strategy: strategy
            })
        });

        removeTypingIndicator();

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        addMessageToChat('bot', data.answer, data);

    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.');
    } finally {
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
    }
}

function addMessageToChat(sender, message, data = null) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = sender === 'user' ? 'You' : 'Research Assistant';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = message;
    
    messageDiv.appendChild(header);
    messageDiv.appendChild(content);
    
    if (data && data.sources && data.sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources-list small text-muted mt-2';
        sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' + 
            data.sources.map((source, index) => 
                `${index + 1}. ${source}`
            ).join('<br>');
        messageDiv.appendChild(sourcesDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-header">Research Assistant</div>
        <div class="message-content">Typing <span>.</span><span>.</span><span>.</span></div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) typingIndicator.remove();
}

async function clearHistory() {
    if (confirm('Clear conversation history?')) {
        document.getElementById('chatMessages').innerHTML = '';
    }
}

document.getElementById('questionInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});