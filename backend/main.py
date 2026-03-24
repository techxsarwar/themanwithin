import os
import secrets
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import (
    get_db, Announcement, SEOSetting, Analytics, SiteSetting, Review, Message,
    AnnouncementCreate, AnnouncementUpdate, SEOSettingUpdate,
    SiteSettingUpdate, ReviewCreate
)

app = FastAPI(title="The Man Within - Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def register_hit(db=Depends(get_db)):
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
