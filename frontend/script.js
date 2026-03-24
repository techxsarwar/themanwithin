let API_BASE_URL = window.location.origin;

// If the user opens the file directly (file://), fall back to production API
if (window.location.protocol === 'file:') {
    API_BASE_URL = "https://themanwithin.onrender.com";
    console.warn("Running via file:// protocol. Falling back to production API:", API_BASE_URL);
}

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Navigation Scrolled State
    const navbar = document.getElementById('navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 2. Smooth Scrolling for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if(targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                // Adjust scroll position for fixed header
                const headerOffset = 80;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
  
                window.scrollTo({
                    top: offsetPosition,
                    behavior: "smooth"
                });
            }
        });
    });

    // 3. Scroll Reveal Animations utilizing Intersection Observer
    function reveal() {
        const reveals = document.querySelectorAll('.reveal');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    // Optional: Stop observing once revealed
                    // observer.unobserve(entry.target);
                }
            });
        }, { 
            threshold: 0.15, // trigger when 15% visible
            rootMargin: "0px 0px -50px 0px"
        });

        reveals.forEach(reveal => {
            observer.observe(reveal);
        });
    }
    
    // Initialize reveal
    reveal();
    
    // Also trigger reveal for elements strictly in view right after load
    setTimeout(() => {
        const reveals = document.querySelectorAll('.reveal');
        reveals.forEach(reveal => {
            const windowHeight = window.innerHeight;
            const elementTop = reveal.getBoundingClientRect().top;
            const elementVisible = 50;
            
            if (elementTop < windowHeight - elementVisible) {
                reveal.classList.add('active');
            }
        });
    }, 100);
    // 4. Mobile Menu Toggle Logic
    const mobileToggle = document.getElementById('mobile-toggle');
    const navLinksList = document.querySelector('.nav-links');

    if (mobileToggle && navLinksList) {
        mobileToggle.addEventListener('click', () => {
            navLinksList.classList.toggle('active');
            // Toggle icon
            const icon = mobileToggle.querySelector('i');
            if (navLinksList.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // Close menu when clicking a link
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', () => {
                navLinksList.classList.remove('active');
                const icon = mobileToggle.querySelector('i');
                if(icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            });
        });
    }

    // 5. Contact Form Submission Handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const formStatus = document.getElementById('formStatus');
            const originalBtnText = submitBtn.textContent;
            
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const subject = document.getElementById('subject').value;
            const message = document.getElementById('message').value;

            // Loading state
            submitBtn.disabled = true;
            submitBtn.textContent = "Sending...";
            formStatus.style.display = 'none';

            try {
                const response = await fetch(`${API_BASE_URL}/api/contact`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, email, subject, message })
                });

                const result = await response.json();

                if (response.ok) {
                    formStatus.textContent = result.message;
                    formStatus.style.color = 'var(--text-light)';
                    formStatus.style.backgroundColor = 'rgba(16, 185, 129, 0.2)'; // Green tint
                    formStatus.style.border = '1px solid rgba(16, 185, 129, 0.4)';
                    formStatus.style.display = 'block';
                    contactForm.reset();
                } else {
                    throw new Error(result.message || "Failed to send message");
                }
            } catch (error) {
                formStatus.textContent = "Error: " + error.message;
                formStatus.style.color = '#ef4444'; // Red color
                formStatus.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                formStatus.style.border = '1px solid rgba(239, 68, 68, 0.3)';
                formStatus.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
        });
    }
    
    // 6. Register Analytics Hit Automatically
    try {
        fetch(`${API_BASE_URL}/api/analytics/hit`, { method: 'POST' }).catch(e => console.error("Analytics error", e));
    } catch(e) {}

    // 7. Load Featured Announcement across the site
    const modal = document.getElementById('announcement-modal');
    if (modal && !sessionStorage.getItem('announcementSeen')) {
        fetch(`${API_BASE_URL}/api/admin/announcements`)
            .then(res => res.json())
            .then(data => {
                if (data && data.length > 0) {
                    const latest = data[0]; 
                    document.getElementById('modal-title').textContent = latest.title;
                    
                    const fullText = latest.content;
                    const charLimit = 200;
                    const descEl = document.getElementById('modal-desc');
                    const readMoreContainer = document.getElementById('modal-read-more-container');
                    
                    if (fullText.length > charLimit) {
                        descEl.textContent = fullText.substring(0, charLimit) + '...';
                        
                        const readMoreBtn = document.createElement('a');
                        readMoreBtn.href = "#";
                        readMoreBtn.className = "btn btn-secondary";
                        readMoreBtn.style.padding = "0.5rem 1.2rem";
                        readMoreBtn.style.fontSize = "0.9rem";
                        readMoreBtn.innerHTML = 'Read More <i class="fas fa-chevron-down" style="margin-left:5px"></i>';
                        
                        readMoreBtn.onclick = (e) => {
                            e.preventDefault();
                            descEl.textContent = fullText;
                            readMoreContainer.style.display = 'none';
                        };
                        readMoreContainer.appendChild(readMoreBtn);
                    } else {
                        descEl.textContent = fullText;
                    }
                    
                    const imageContainer = document.getElementById('modal-image-container');
                    if(latest.image_url) {
                        imageContainer.style.backgroundImage = `url('${latest.image_url}')`;
                    } else {
                        imageContainer.style.display = 'none';
                    }
                    
                    modal.style.display = 'flex';
                }
            })
            .catch(err => console.error("Failed to load announcements:", err));
    }

    // 8. Load Public Testimonials if on Reviews page
    const publicReviewsContainer = document.getElementById('public-reviews-container');
    if (publicReviewsContainer) {
        fetch(`${API_BASE_URL}/api/reviews`)
            .then(res => res.json())
            .then(reviews => {
                if (!reviews || reviews.length === 0) {
                    publicReviewsContainer.innerHTML = '<div style="text-align:center; padding:3rem; color:var(--text-muted); grid-column: 1 / -1;">No reviews yet. Check back soon!</div>';
                    return;
                }
                
                publicReviewsContainer.innerHTML = reviews.map(rev => {
                    const stars = '<i class="fas fa-star"></i>'.repeat(rev.rating) + '<i class="far fa-star"></i>'.repeat(5 - rev.rating);
                    return `
                    <div class="review-card glass-panel reveal active">
                        <div class="review-header">
                            <h4>${escapeHTML(rev.name)}</h4>
                            <div class="review-stars">${stars}</div>
                        </div>
                        <div class="review-date">${new Date(rev.created_at).toLocaleDateString()}</div>
                        <p class="review-text">"${escapeHTML(rev.text)}"</p>
                    </div>
                `}).join('');
            })
            .catch(err => {
                publicReviewsContainer.innerHTML = '<div style="color:#ef4444; padding:2rem; text-align:center; grid-column: 1 / -1;">Failed to load reviews.</div>';
            });
    }
});

// Utility HTML escape generic string function
function escapeHTML(str) {
    if(!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag]));
}

// Global modal closer exposed to window so onclick works
window.closeAnnouncementModal = function() {
    const modal = document.getElementById('announcement-modal');
    if(modal) {
        modal.style.display = 'none';
        sessionStorage.setItem('announcementSeen', 'true');
    }
}

// --- Community Chat Logic ---
let chatWs = null;
let currentChatUser = localStorage.getItem('chatUser');
let currentChatIsAdmin = localStorage.getItem('chatIsAdmin') === 'true';

// Explicitly build WebSocket URL based on current host
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const CHAT_WS_URL = `${wsProtocol}//${window.location.host}/ws/chat`;
let heartbeatInterval = null;

// Auto-join if already logged in on community page
document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the community page by looking for the chat container
    if (document.getElementById('community-chat-container')) {
        if (currentChatUser) {
            showChatInterface();
        }
    }
});

function showChatInterface() {
    const authScreen = document.getElementById('chat-auth-screen');
    const chatScreen = document.getElementById('chat-interface-screen');
    const userDisplay = document.getElementById('active-user-display');
    
    if (authScreen) authScreen.style.display = 'none';
    if (chatScreen) chatScreen.style.display = 'flex';
    if (userDisplay) userDisplay.textContent = `Active as: ${currentChatUser}`;
    
    loadChatHistory();
    connectWebSocket();
}

async function joinChat(type) {
    if (type === 'admin') {
        const pass = document.getElementById('chat-admin-pass').value;
        if (pass !== 'admin') {
            alert("Incorrect admin password.");
            return;
        }
        currentChatUser = "Faisal Rasool | Author";
        currentChatIsAdmin = true;
    } else {
        const name = document.getElementById('chat-guest-name').value.trim();
        if (!name) {
            alert("Please enter a name.");
            return;
        }
        currentChatUser = name;
        currentChatIsAdmin = false;
    }

    // Persist session
    localStorage.setItem('chatUser', currentChatUser);
    localStorage.setItem('chatIsAdmin', currentChatIsAdmin);

    showChatInterface();
}

async function loadChatHistory() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/chat/history`);
        if (res.ok) {
            const history = await res.json();
            const container = document.getElementById('chat-messages');
            container.innerHTML = '';
            history.forEach(msg => appendMessageToChat(msg));
            scrollToChatBottom();
        }
    } catch(e) {
        console.error("Failed to load chat history", e);
    }
}

function connectWebSocket() {
    console.log("Attempting WebSocket connection to:", CHAT_WS_URL);
    chatWs = new WebSocket(CHAT_WS_URL);
    
    chatWs.onopen = () => {
        console.log("WebSocket connection established!");
        chatWs.send(JSON.stringify({
            type: "join",
            sender: currentChatUser
        }));
        
        // Start heartbeat to keep Render connection alive
        if (heartbeatInterval) clearInterval(heartbeatInterval);
        heartbeatInterval = setInterval(() => {
            if (chatWs && chatWs.readyState === WebSocket.OPEN) {
                chatWs.send(JSON.stringify({ type: "ping" }));
            }
        }, 30000);
    };

    chatWs.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === "pong") return; // Ignore heartbeat response
            console.log("Received message:", msg);
            appendMessageToChat(msg);
            scrollToChatBottom();
        } catch(e) {
            console.error("Error parsing WebSocket message:", e);
        }
    };

    chatWs.onerror = (error) => {
        console.error("WebSocket Error Details:", error);
    };

    chatWs.onclose = (event) => {
        console.warn("WebSocket connection closed:", event.code, event.reason);
        if (heartbeatInterval) clearInterval(heartbeatInterval);
        setTimeout(connectWebSocket, 5000);
    };
}

function appendMessageToChat(msg) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    
    if (msg.is_system) {
        div.className = "chat-msg system";
        div.textContent = msg.text;
    } else {
        const isSelf = msg.sender === currentChatUser && msg.is_admin === currentChatIsAdmin;
        div.className = `chat-msg ${isSelf ? 'self' : ''}`;
        
        const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
        const adminTick = msg.is_admin ? '<i class="fas fa-check-circle" title="Verified Author" style="color:#1da1f2; margin-left: 5px;"></i>' : '';
        const senderClass = msg.is_admin ? 'admin' : '';
        
        div.innerHTML = `
            <div class="chat-msg-header">
                <span class="chat-msg-sender ${senderClass}">${escapeHTML(msg.sender)}${adminTick}</span>
                <span>${time}</span>
            </div>
            <div class="chat-msg-text">${escapeHTML(msg.text)}</div>
        `;
    }
    container.appendChild(div);
}

function scrollToChatBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || !chatWs) return;

    chatWs.send(JSON.stringify({
        sender: currentChatUser,
        is_admin: currentChatIsAdmin,
        text: text
    }));
    input.value = '';
}

function handleChatKeyPress(e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
}
