import os
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contact.db")

# PostgreSQL / Supabase DB Setup
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---

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

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    visit_count = Column(Integer, default=0)

class SiteSetting(Base):
    __tablename__ = "site_settings"
    id = Column(Integer, primary_key=True, index=True)
    youtube_url = Column(String, default="")
    instagram_url = Column(String, default="")
    github_url = Column(String, default="")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    rating = Column(Integer)
    text = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    subject = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    is_admin = Column(Boolean, default=False)
    text = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class BannedUser(Base):
    __tablename__ = "banned_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    banned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AdminCredentials(Base):
    __tablename__ = "admin_credentials"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password_hash = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schemas ---

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

class SiteSettingUpdate(BaseModel):
    youtube_url: Optional[str] = None
    instagram_url: Optional[str] = None
    github_url: Optional[str] = None

class ReviewCreate(BaseModel):
    name: str
    rating: int
    text: str

class BannedUserCreate(BaseModel):
    username: str

class ChatTimerSet(BaseModel):
    duration_seconds: int

class AdminCredentialsUpdate(BaseModel):
    old_username: str
    old_password: str
    new_username: str
    new_password: str
