document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const quickReplyContainer = document.getElementById('quick-reply-container');
    
    // Load categories for quick replies
    loadCategories();
    
    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Focus on input when the page loads
    userInput.focus();
    
    // Scroll to bottom of messages container
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Add message to the chat
    function addMessage(message, isUser = false, source = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'bot');
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        const paragraph = document.createElement('p');
        paragraph.textContent = message;
        
        messageContent.appendChild(paragraph);
        messageDiv.appendChild(messageContent);
        
        // Add source badge if provided
        if (source && !isUser) {
            const sourceBadge = document.createElement('span');
            sourceBadge.classList.add('badge', 'source-badge');
            
            if (source === 'nltk') {
                sourceBadge.classList.add('bg-success');
                sourceBadge.textContent = 'via NLTK';
            } else if (source === 'rag') {
                sourceBadge.classList.add('bg-info');
                sourceBadge.textContent = 'via RAG';
            } else if (source === 'error') {
                sourceBadge.classList.add('bg-danger');
                sourceBadge.textContent = 'Error';
            } else {
                sourceBadge.classList.add('bg-secondary');
                sourceBadge.textContent = source;
            }
            
            messageDiv.appendChild(sourceBadge);
        }
        
        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        typingIndicator.classList.remove('d-none');
        scrollToBottom();
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.classList.add('d-none');
    }
    
    // Disable/enable input during processing
    function setInputState(disabled) {
        userInput.disabled = disabled;
        sendButton.disabled = disabled;
        
        // Also disable quick reply buttons
        const quickReplyButtons = document.querySelectorAll('.quick-reply-btn');
        quickReplyButtons.forEach(btn => {
            btn.disabled = disabled;
        });
    }
    
    // Send user message to the backend
    function sendMessage() {
        const message = userInput.value.trim();
        
        // Don't send empty messages
        if (!message) {
            return;
        }
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input
        userInput.value = '';
        
        // Show typing indicator and disable input
        showTypingIndicator();
        setInputState(true);
        
        // Send request to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Short delay to make typing indicator visible
            setTimeout(() => {
                // Hide typing indicator and enable input
                hideTypingIndicator();
                setInputState(false);
                
                // Add bot response to chat
                addMessage(data.reply, false, data.source);
                
                // Focus on input for next message
                userInput.focus();
            }, 500);
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Hide typing indicator and enable input
            hideTypingIndicator();
            setInputState(false);
            
            // Add error message to chat
            addMessage("Sorry, I encountered an error processing your request. Please try again later.", false, "error");
            
            // Focus on input for next message
            userInput.focus();
        });
    }
    
    // Load categories for quick replies
    function loadCategories() {
        fetch('/categories')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(categories => {
                // Create quick reply buttons
                categories.forEach(category => {
                    const button = document.createElement('button');
                    button.classList.add('btn', 'btn-outline-secondary', 'quick-reply-btn');
                    button.textContent = category;
                    
                    button.addEventListener('click', function() {
                        // Set input value to category
                        userInput.value = `Tell me about ${category}`;
                        
                        // Send message
                        sendMessage();
                    });
                    
                    quickReplyContainer.appendChild(button);
                });
            })
            .catch(error => {
                console.error('Error loading categories:', error);
                // Add a fallback button if categories fail to load
                const fallbackButton = document.createElement('button');
                fallbackButton.classList.add('btn', 'btn-outline-secondary', 'quick-reply-btn');
                fallbackButton.textContent = "Need Help";
                
                fallbackButton.addEventListener('click', function() {
                    userInput.value = "What can you help me with?";
                    sendMessage();
                });
                
                quickReplyContainer.appendChild(fallbackButton);
            });
    }
});
