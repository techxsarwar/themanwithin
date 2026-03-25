import os
import secrets
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import (
    get_db, SessionLocal, Announcement, SEOSetting, Analytics, SiteSetting, Review, Message, ChatMessage,
    BannedUser, AnnouncementCreate, AnnouncementUpdate, SEOSettingUpdate,
    SiteSettingUpdate, ReviewCreate, BannedUserCreate, ChatTimerSet
)

app = FastAPI(title="The Man Within - Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://themanwithin.onrender.com",
        "https://themanwithin.netlify.app",
        "https://the-man-within.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# DB Configuration and Models are now efficiently refactored into models.py


security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "faisal")
    correct_password = secrets.compare_digest(credentials.password, "admin")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Mount assets directory for static files (images, etc)
assets_dir = os.path.join(FRONTEND_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Pydantic model for contact form data
class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str = ""
    message: str

# --- WebSocket Chat Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}
        self.chat_frozen_until: datetime = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = None

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_json(message)
            except Exception:
                pass

    def set_user(self, websocket: WebSocket, username: str):
        if websocket in self.active_connections:
            self.active_connections[websocket] = username

manager = ConnectionManager()

# Endpoints for serving static HTML pages
@app.get("/", response_class=FileResponse)
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{page}.html", response_class=FileResponse)
async def read_html_page(page: str):
    file_path = os.path.join(FRONTEND_DIR, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)

# Endpoints for serving CSS and JS
@app.get("/styles.css", response_class=FileResponse)
async def read_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "styles.css"))

@app.get("/script.js", response_class=FileResponse)
async def read_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))

# API endpoint for handling contact form submissions
@app.post("/api/contact")
async def handle_contact_form(message: ContactMessage, db=Depends(get_db)):
    try:
        db_msg = Message(
            name=message.name, 
            email=message.email, 
            subject=message.subject, 
            message=message.message
        )
        db.add(db_msg)
        db.commit()
        return JSONResponse(content={
            "status": "success", 
            "message": "Thank you! Your message has been received."
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    login_path = os.path.join(FRONTEND_DIR, "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return HTMLResponse("<h1>login.html missing</h1>", status_code=404)

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return HTMLResponse("<h1>admin.html missing</h1>", status_code=404)

@app.get("/api/admin/messages")
async def get_admin_messages(db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        return db.query(Message).order_by(Message.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/messages/{id}")
async def delete_admin_message(id: int, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_msg = db.query(Message).filter(Message.id == id).first()
        if not db_msg:
            raise HTTPException(status_code=404, detail="Message not found")
        db.delete(db_msg)
        db.commit()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Announcement Endpoints
@app.get("/api/admin/announcements")
async def get_announcements(db=Depends(get_db)):
    try:
        return db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/announcements")
async def create_announcement(announcement: AnnouncementCreate, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_announcement = Announcement(**announcement.model_dump())
        db.add(db_announcement)
        db.commit()
        db.refresh(db_announcement)
        return db_announcement
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/announcements/{id}")
async def update_announcement(id: int, announcement: AnnouncementUpdate, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_announcement = db.query(Announcement).filter(Announcement.id == id).first()
        if not db_announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        update_data = announcement.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(db_announcement, key, value)
                
        db.commit()
        db.refresh(db_announcement)
        return db_announcement
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/announcements/{id}")
async def delete_announcement(id: int, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_announcement = db.query(Announcement).filter(Announcement.id == id).first()
        if not db_announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
        db.delete(db_announcement)
        db.commit()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# SEO Endpoints
@app.get("/api/admin/seo")
async def get_seo_settings(db=Depends(get_db)):
    try:
        return db.query(SEOSetting).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/seo/{page_name}")
async def update_seo_setting(page_name: str, seo: SEOSettingUpdate, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_seo = db.query(SEOSetting).filter(SEOSetting.page_name == page_name).first()
        if not db_seo:
            db_seo = SEOSetting(page_name=page_name, title=seo.title, description=seo.description)
            db.add(db_seo)
        else:
            db_seo.title = seo.title
            db_seo.description = seo.description
        db.commit()
        db.refresh(db_seo)
        return db_seo
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/analytics")
async def get_analytics(db=Depends(get_db)):
    try:
        stat = db.query(Analytics).first()
        if not stat:
            stat = Analytics(visit_count=0)
            db.add(stat)
            db.commit()
            db.refresh(stat)
        return {"visit_count": stat.visit_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/hit")
async def register_hit(data: dict = None, db=Depends(get_db)):
    try:
        stat = db.query(Analytics).first()
        if not stat:
            stat = Analytics(visit_count=1)
            db.add(stat)
        else:
            stat.visit_count += 1
        db.commit()
        return {"status": "success", "visit_count": stat.visit_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Media & Social Settings Endpoints
@app.get("/api/site-settings")
async def get_site_settings(db=Depends(get_db)):
    try:
        settings = db.query(SiteSetting).first()
        if not settings:
            settings = SiteSetting()
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/site-settings")
async def update_site_settings(settings_update: SiteSettingUpdate, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        settings = db.query(SiteSetting).first()
        if not settings:
            settings = SiteSetting(**settings_update.model_dump(exclude_unset=True))
            db.add(settings)
        else:
            update_data = settings_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    setattr(settings, key, value)
        db.commit()
        db.refresh(settings)
        return settings
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Testimonials/Reviews Endpoints
@app.get("/api/reviews")
async def get_reviews(db=Depends(get_db)):
    try:
        return db.query(Review).order_by(Review.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reviews")
async def create_review(review: ReviewCreate, db=Depends(get_db)):
    try:
        db_review = Review(**review.model_dump())
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        return db_review
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reviews/{id}")
async def delete_review(id: int, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        db_review = db.query(Review).filter(Review.id == id).first()
        if not db_review:
            raise HTTPException(status_code=404, detail="Review not found")
        db.delete(db_review)
        db.commit()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Community Chat Endpoints
@app.get("/api/chat/history")
async def get_chat_history(db=Depends(get_db)):
    try:
        msgs = db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(100).all()
        return [
            {
                "id": m.id,
                "sender": m.sender,
                "is_admin": m.is_admin,
                "text": m.text,
                "timestamp": m.created_at.isoformat() if m.created_at else ""
            } for m in reversed(msgs)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/messages/{id}")
async def delete_chat_message(id: int, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        msg = db.query(ChatMessage).filter(ChatMessage.id == id).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        db.delete(msg)
        db.commit()
        await manager.broadcast({"type": "delete", "id": id})
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/chat/users")
async def get_active_chat_users(username: str = Depends(get_current_username)):
    users = [u for u in manager.active_connections.values() if u is not None]
    return {"users": list(set(users))}

@app.post("/api/admin/chat/ban")
async def ban_chat_user(user_data: BannedUserCreate, db=Depends(get_db), username: str = Depends(get_current_username)):
    try:
        existing = db.query(BannedUser).filter(BannedUser.username == user_data.username).first()
        if not existing:
            bu = BannedUser(username=user_data.username)
            db.add(bu)
            db.commit()
            
        websockets_to_close = []
        for ws, uname in manager.active_connections.items():
            if uname == user_data.username:
                websockets_to_close.append(ws)
                
        for ws in websockets_to_close:
            try:
                await ws.send_json({"type": "banned", "text": "You have been banned by the author."})
                await ws.close()
            except Exception:
                pass
            manager.disconnect(ws)
            
        return {"status": "success", "message": f"{user_data.username} banned."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/chat/timer")
async def set_chat_timer(timer_data: ChatTimerSet, username: str = Depends(get_current_username)):
    if timer_data.duration_seconds > 0:
        manager.chat_frozen_until = datetime.now() + timedelta(seconds=timer_data.duration_seconds)
        await manager.broadcast({"type": "freeze", "duration": timer_data.duration_seconds})
    else:
        manager.chat_frozen_until = None
        await manager.broadcast({"type": "freeze", "duration": 0})
    return {"status": "success"}

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    print(f"New chat connection attempt: {websocket.client}")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_data = json.loads(data)
                
                # Handle Heartbeat
                if msg_data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                sender = msg_data.get("sender", "Guest")
                
                # Check Ban status
                db = SessionLocal()
                is_banned = db.query(BannedUser).filter(BannedUser.username == sender).first()
                db.close()
                if is_banned:
                    await websocket.send_json({"type": "banned", "text": "You are banned from the chat."})
                    manager.disconnect(websocket)
                    await websocket.close()
                    break

                # If a join event, system announces
                if msg_data.get("type") == "join":
                    manager.set_user(websocket, sender)
                    welcome_text = f"The Man Within welcomes {sender} to the chat!"
                    broadcast_data = {
                        "sender": "The Man Within",
                        "is_admin": True,
                        "text": welcome_text,
                        "timestamp": datetime.now().isoformat(),
                        "is_system": True
                    }
                    await manager.broadcast(broadcast_data)
                    continue

                # Normal Chat Message
                if manager.chat_frozen_until and datetime.now() < manager.chat_frozen_until:
                    # Chat is frozen
                    continue

                text = msg_data.get("text", "")
                is_admin = msg_data.get("is_admin", False)
                
                # Scope DB connection to message processing strictly
                db = SessionLocal()
                try:
                    db_msg = ChatMessage(sender=sender, text=text, is_admin=is_admin)
                    db.add(db_msg)
                    db.commit()
                    db.refresh(db_msg)
                    
                    broadcast_data = {
                        "id": db_msg.id,
                        "sender": db_msg.sender,
                        "is_admin": db_msg.is_admin,
                        "text": db_msg.text,
                        "timestamp": db_msg.created_at.isoformat()
                    }
                finally:
                    db.close()
                    
                await manager.broadcast(broadcast_data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"Chat WS error processing message: {e}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

