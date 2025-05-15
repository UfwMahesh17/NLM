document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const quickReplyContainer = document.getElementById('quick-reply-container');
    const auroraBackground = document.getElementById('aurora-background');
    
    // Keep track of conversation history
    let conversationHistory = [];
    
    // Initialize the Aurora background effect
    initAuroraEffect();
    
    // Initialize quick reply buttons for categories
    initializeQuickReplies();
    
    // Create subtle Aurora background effect
    function initAuroraEffect() {
        const canvas = document.createElement('canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        auroraBackground.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        
        // Aurora effects don't need character sets
        
        // Font size
        const fontSize = 14;
        
        // Calculate columns
        const columns = Math.floor(canvas.width / fontSize);
        
        // Array for drops
        const drops = [];
        for (let i = 0; i < columns; i++) {
            drops[i] = Math.floor(Math.random() * -canvas.height);
        }
        
        // Create the Aurora effect
        function drawAuroraEffect() {
            // Clear canvas with transparent background
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Create gradient background
            const time = Date.now() * 0.001;
            
            // Draw flowing aurora waves
            for (let i = 0; i < 5; i++) {
                // Create gradient for each wave
                const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
                
                // Aurora colors
                gradient.addColorStop(0, `rgba(106, 17, 203, ${0.02 + i * 0.01})`);
                gradient.addColorStop(0.5, `rgba(37, 117, 252, ${0.02 + i * 0.01})`);
                gradient.addColorStop(1, `rgba(200, 80, 192, ${0.01 + i * 0.005})`);
                
                ctx.fillStyle = gradient;
                ctx.beginPath();
                
                // Draw flowing wave
                for (let x = 0; x < canvas.width; x += 5) {
                    const y = Math.sin((x * 0.01) + (time + i)) * 50 + 
                             Math.sin((x * 0.02) + (time * 0.8 + i)) * 30 +
                             (canvas.height * (0.2 + i * 0.05));
                             
                    if (x === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                }
                
                // Complete the path
                ctx.lineTo(canvas.width, canvas.height);
                ctx.lineTo(0, canvas.height);
                ctx.closePath();
                ctx.fill();
            }
            
            // Add subtle sparkles
            for (let i = 0; i < 20; i++) {
                const x = Math.random() * canvas.width;
                const y = Math.random() * canvas.height * 0.6;
                const size = Math.random() * 2 + 1;
                const opacity = Math.random() * 0.5 + 0.2;
                
                // Create glow
                ctx.beginPath();
                ctx.arc(x, y, size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${opacity * Math.sin(time * 2) * 0.5 + 0.5})`;
                ctx.shadowBlur = 10;
                ctx.shadowColor = 'rgba(106, 17, 203, 0.8)';
                ctx.fill();
            }
        }
        
        // Run the animation
        setInterval(drawAuroraEffect, 50);
        
        // Handle window resize
        window.addEventListener('resize', function() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    }
    
    // Scroll to bottom of messages
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Add message to the chat
    function addMessage(text, isUser = false, source = '') {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user' : 'bot');
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        // For bot messages, add with typing effect
        if (!isUser) {
            const paragraph = document.createElement('p');
            messageContent.appendChild(paragraph);
            
            // Add source badge
            const sourceBadge = document.createElement('span');
            sourceBadge.classList.add('badge', 'bg-secondary', 'source-badge');
            sourceBadge.textContent = source;
            messageDiv.appendChild(sourceBadge);
            
            // Add to DOM first
            messageDiv.appendChild(messageContent);
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
            
            // Then animate typing effect for bot messages
            let i = 0;
            const speed = 20; // typing speed in ms
            
            function typeWriter() {
                if (i < text.length) {
                    paragraph.textContent += text.charAt(i);
                    i++;
                    scrollToBottom();
                    setTimeout(typeWriter, speed);
                } else {
                    // Remove cursor animation when done typing
                    paragraph.style.borderRight = 'none';
                }
            }
            
            typeWriter();
        } else {
            // For user messages, just add the text directly
            messageContent.innerHTML = `<p>${text}</p>`;
            messageDiv.appendChild(messageContent);
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }
        
        // Add to conversation history
        conversationHistory.push({
            text: text,
            isUser: isUser,
            source: source
        });
        
        return messageDiv;
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
    
    // Initialize quick reply buttons
    function initializeQuickReplies() {
        fetch('/api/categories')
            .then(response => response.json())
            .then(data => {
                if (data.categories && data.categories.length > 0) {
                    quickReplyContainer.innerHTML = '';
                    
                    data.categories.forEach(category => {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.classList.add('btn', 'quick-reply-btn');
                        button.textContent = category;
                        
                        button.addEventListener('click', () => {
                            handleCategoryClick(category);
                        });
                        
                        quickReplyContainer.appendChild(button);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching categories:', error);
            });
    }
    
    // Handle category button click
    function handleCategoryClick(category) {
        fetch(`/api/category_questions?category=${encodeURIComponent(category)}`)
            .then(response => response.json())
            .then(data => {
                if (data.questions && data.questions.length > 0) {
                    // Clear current quick replies
                    quickReplyContainer.innerHTML = '';
                    
                    // Add back button
                    const backButton = document.createElement('button');
                    backButton.type = 'button';
                    backButton.classList.add('btn', 'quick-reply-btn');
                    backButton.innerHTML = '<i class="fas fa-arrow-left"></i> Back';
                    backButton.addEventListener('click', initializeQuickReplies);
                    quickReplyContainer.appendChild(backButton);
                    
                    // Add questions as quick reply buttons
                    data.questions.forEach(question => {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.classList.add('btn', 'quick-reply-btn');
                        
                        // Truncate long questions
                        button.textContent = question.length > 40 ? 
                            question.substring(0, 37) + '...' : 
                            question;
                        
                        // Set full question as data attribute
                        button.dataset.fullQuestion = question;
                        
                        button.addEventListener('click', () => {
                            const fullQuestion = button.dataset.fullQuestion;
                            sendMessage(fullQuestion);
                            // Reset to category buttons after selection
                            setTimeout(initializeQuickReplies, 1000);
                        });
                        
                        quickReplyContainer.appendChild(button);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching questions:', error);
            });
    }
    
    // Send a message to the server and get a response
    function sendMessage(text, useRAG = false) {
        // Don't send empty messages
        if (!text.trim()) return;
        
        // Add user message to chat
        addMessage(text, true);
        
        // Clear input field
        userInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Use Aurora transition effect for longer responses
        if (useRAG) {
            addAuroraTransitionEffect();
        }
        
        // Send message to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                use_rag: useRAG
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response to chat
            if (data.error) {
                addMessage(`Error: ${data.error}`, false, 'error');
            } else {
                addMessage(data.response, false, data.source || 'unknown');
            }
        })
        .catch(error => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add error message
            addMessage('Sorry, I\'m having trouble connecting right now. Please try again later.', false, 'error');
            console.error('Error sending message:', error);
        });
    }
    
    // Add Aurora transition effect (for complex queries)
    function addAuroraTransitionEffect() {
        // Only add if not already in the DOM
        if (!document.querySelector('.aurora-transition')) {
            const transition = document.createElement('div');
            transition.classList.add('aurora-transition');
            document.body.appendChild(transition);
            
            // Add shimmering aurora overlay
            const auroraOverlay = document.createElement('div');
            auroraOverlay.classList.add('aurora-shimmer');
            transition.appendChild(auroraOverlay);
            
            // Trigger animation
            setTimeout(() => {
                transition.classList.add('active');
                
                // Remove after animation completes
                setTimeout(() => {
                    transition.classList.remove('active');
                    setTimeout(() => {
                        transition.remove();
                    }, 500);
                }, 1000);
            }, 10);
        }
    }
    
    // Event listeners
    sendButton.addEventListener('click', () => {
        const text = userInput.value.trim();
        const isComplexQuery = text.length > 50 || text.includes('?') && text.length > 30;
        sendMessage(text, isComplexQuery);
    });
    
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const text = userInput.value.trim();
            const isComplexQuery = text.length > 50 || text.includes('?') && text.length > 30;
            sendMessage(text, isComplexQuery);
        }
    });
    
    // Auto-focus the input field
    userInput.focus();
    
    // Add subtle background particle effect (purely visual)
    function createAuroraParticleEffect() {
        const canvas = document.createElement('canvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.zIndex = '-2';
        canvas.style.opacity = '0.1';
        document.body.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        
        // Aurora particles
        const particles = [];
        const particleCount = 50;
        
        // Create particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 3 + 1,
                speedX: Math.random() * 0.5 - 0.25,
                speedY: Math.random() * 0.5 - 0.25,
                color: getRandomAuroraColor(),
                opacity: Math.random() * 0.7 + 0.3,
                trail: []
            });
        }
        
        // Get random aurora color
        function getRandomAuroraColor() {
            const colors = [
                'rgba(106, 17, 203, 0.7)',
                'rgba(37, 117, 252, 0.7)',
                'rgba(248, 87, 166, 0.7)',
                'rgba(176, 108, 255, 0.7)',
                'rgba(66, 191, 223, 0.7)'
            ];
            return colors[Math.floor(Math.random() * colors.length)];
        }
        
        // Draw aurora particles
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(p => {
                // Update position
                p.x += p.speedX;
                p.y += p.speedY;
                
                // Add to trail (with maximum length)
                p.trail.push({x: p.x, y: p.y});
                if (p.trail.length > 20) {
                    p.trail.shift();
                }
                
                // Draw trail
                if (p.trail.length > 1) {
                    ctx.beginPath();
                    ctx.moveTo(p.trail[0].x, p.trail[0].y);
                    
                    for (let i = 1; i < p.trail.length; i++) {
                        ctx.lineTo(p.trail[i].x, p.trail[i].y);
                    }
                    
                    ctx.strokeStyle = p.color;
                    ctx.lineWidth = p.size / 2;
                    ctx.stroke();
                }
                
                // Draw particle
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();
                
                // Wrap around edges
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;
                
                // Randomly change direction occasionally
                if (Math.random() < 0.01) {
                    p.speedX = Math.random() * 0.5 - 0.25;
                    p.speedY = Math.random() * 0.5 - 0.25;
                }
            });
        }
        
        // Call draw function at intervals
        setInterval(draw, 30);
        
        // Resize canvas on window resize
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    }
    
    // Initialize subtle background effect
    createAuroraParticleEffect();
});
