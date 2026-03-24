import os

html_files = [f for f in os.listdir('frontend') if f.endswith('.html') and f not in ['index.html', 'login.html', 'admin.html', '404.html']]

widget_html = """    <!-- Chat Widget -->
    <div id="chat-widget-btn" class="chat-widget-btn" onclick="openChatModal()">
        <i class="fas fa-comment-dots"></i>
    </div>

    <!-- Chat Modal -->
    <div id="chat-modal" class="chat-overlay" style="display: none;">
        <div class="chat-container glass-panel">
            <div class="chat-header">
                <h3><i class="fas fa-users"></i> The Man Within Community</h3>
                <button class="close-chat" onclick="closeChatModal()"><i class="fas fa-times"></i></button>
            </div>
            
            <!-- Auth Screen -->
            <div id="chat-auth-screen" class="chat-screen active">
                <p>Join the conversation with other readers.</p>
                <div style="margin-top: 1rem;">
                    <input type="text" id="chat-guest-name" class="form-control" placeholder="Enter name (e.g. John)">
                    <button class="btn btn-secondary" onclick="joinChat('guest')" style="width: 100%; margin-top: 10px;">Join as Guest</button>
                </div>
                
                <div class="divider" style="margin: 2rem 0; background: rgba(255,255,255,0.1);"></div>
                
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">Admin Login</p>
                <input type="password" id="chat-admin-pass" class="form-control" placeholder="Admin Password">
                <button class="btn btn-primary" onclick="joinChat('admin')" style="width: 100%; margin-top: 10px;">Login as Author</button>
            </div>

            <!-- Chat Screen -->
            <div id="chat-interface-screen" class="chat-screen" style="display: none; padding: 0;">
                <div id="chat-messages" class="chat-messages" style="padding: 1.5rem;">
                    <!-- Messages go here -->
                </div>
                <div class="chat-input-area" style="padding: 1rem 1.5rem; background: rgba(0,0,0,0.3);">
                    <input type="text" id="chat-input" class="form-control" placeholder="Type a message..." onkeypress="handleChatKeyPress(event)">
                    <button class="btn btn-primary" onclick="sendChatMessage()" style="padding: 0 1rem;"><i class="fas fa-paper-plane"></i></button>
                </div>
            </div>
        </div>
    </div>
"""

for file in html_files:
    file_path = os.path.join('frontend', file)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'id="chat-widget-btn"' not in content:
        content = content.replace('</body>', widget_html + '</body>')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
