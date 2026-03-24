import os
import sqlite3
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI(title="The Man Within - Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://themanwithin.netlify.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
DB_PATH = os.path.join(BASE_DIR, "contact.db")

# PostgreSQL / Supabase DB Setup
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    image_url = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SEOSetting(Base):
    __tablename__ = "seo_settings"
    id = Column(Integer, primary_key=True, index=True)
    page_name = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas for new models
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    image_url: str = ""

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None

class SEOSettingUpdate(BaseModel):
    title: str
    description: str

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            subject TEXT,
            message TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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
async def handle_contact_form(message: ContactMessage):
    # Log the message to the console
    print("-" * 40)
    print("NEW CONTACT MESSAGE")
    print(f"Name:    {message.name}")
    print(f"Email:   {message.email}")
    print(f"Subject: {message.subject}")
    print(f"Message: {message.message}")
    print("-" * 40)
    
    # Save to SQLite database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (name, email, subject, message, timestamp) VALUES (?, ?, ?, ?, ?)",
              (message.name, message.email, message.subject, message.message, timestamp))
    conn.commit()
    conn.close()
    
    return JSONResponse(content={
        "status": "success", 
        "message": "Thank you! Your message has been received."
    })

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
async def get_admin_messages(username: str = Depends(get_current_username)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM messages ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Announcement Endpoints
@app.get("/api/admin/announcements")
async def get_announcements(db=Depends(get_db)):
    return db.query(Announcement).order_by(Announcement.created_at.desc()).all()

@app.post("/api/admin/announcements")
async def create_announcement(announcement: AnnouncementCreate, db=Depends(get_db), username: str = Depends(get_current_username)):
    db_announcement = Announcement(**announcement.model_dump())
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement

@app.put("/api/admin/announcements/{id}")
async def update_announcement(id: int, announcement: AnnouncementUpdate, db=Depends(get_db), username: str = Depends(get_current_username)):
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

@app.delete("/api/admin/announcements/{id}")
async def delete_announcement(id: int, db=Depends(get_db), username: str = Depends(get_current_username)):
    db_announcement = db.query(Announcement).filter(Announcement.id == id).first()
    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    db.delete(db_announcement)
    db.commit()
    return {"status": "success"}

# SEO Endpoints
@app.get("/api/admin/seo")
async def get_seo_settings(db=Depends(get_db)):
    return db.query(SEOSetting).all()

@app.put("/api/admin/seo/{page_name}")
async def update_seo_setting(page_name: str, seo: SEOSettingUpdate, db=Depends(get_db), username: str = Depends(get_current_username)):
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
