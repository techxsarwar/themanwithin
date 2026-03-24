import os
import sqlite3
import secrets
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

app = FastAPI(title="The Man Within - Backend", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
DB_PATH = os.path.join(BASE_DIR, "contact.db")

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

# Admin protected endpoints
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(username: str = Depends(get_current_username)):
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return HTMLResponse("<h1>Admin properly authenticated but admin.html missing</h1>")

@app.get("/api/admin/messages")
async def get_admin_messages(username: str = Depends(get_current_username)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM messages ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
