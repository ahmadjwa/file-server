from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
import os
import shutil
import random

app = FastAPI()

# =========================
# DATABASE
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

elif DATABASE_URL.startswith("postgresql"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )
    connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =========================
# USER TABLE
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# =========================
# FILE STORAGE
# =========================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

sessions = {}

def create_session(user):
    sid = str(random.randint(100000, 999999))
    sessions[sid] = user
    return sid

def get_user(sid):
    return sessions.get(sid)

def delete_session(sid):
    if sid in sessions:
        del sessions[sid]

# =========================
# HOME PAGE (LOGIN + REGISTER)
# =========================
@app.get("/", response_class=HTMLResponse)
def home(error: str = ""):

    error_html = f"<div class='error'>{error}</div>" if error else ""

    return f"""
    <html>
    <head>
        <style>
            body {{
                margin:0;
                font-family:Arial;
                background:linear-gradient(135deg,#0f172a,#1e293b);
                color:white;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }}

            .box {{
                background:#111827;
                padding:30px;
                border-radius:15px;
                width:360px;
                box-shadow:0 10px 30px rgba(0,0,0,0.4);
            }}

            input {{
                width:100%;
                padding:10px;
                margin:6px 0;
                border:none;
                border-radius:8px;
                outline:none;
            }}

            button {{
                width:100%;
                padding:10px;
                margin-top:10px;
                border:none;
                border-radius:8px;
                cursor:pointer;
                background:#3b82f6;
                color:white;
                font-weight:bold;
            }}

            button:hover {{
                background:#2563eb;
            }}

            .error {{
                background:#ef4444;
                padding:8px;
                border-radius:6px;
                margin-bottom:10px;
            }}
        </style>
    </head>

    <body>
        <div class="box">
            <h2>☁ Cloud Drive</h2>
            {error_html}

            <h3>Login</h3>
            <form action="/login" method="post">
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button>Login</button>
            </form>

            <h3>Register</h3>
            <form action="/register" method="post">
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button>Create Account</button>
            </form>
        </div>
    </body>
    </html>
    """

# =========================
# REGISTER
# =========================
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()

        if existing:
            return RedirectResponse(url="/?error=Username already exists", status_code=302)

        hashed = pwd_context.hash(password)

        user = User(username=username, password=hashed)
        db.add(user)
        db.commit()

        return RedirectResponse(url="/?error=Account created successfully", status_code=302)

    finally:
        db.close()

# =========================
# LOGIN
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return RedirectResponse(url="/?error=User not found", status_code=302)

        if not pwd_context.verify(password, user.password):
            return RedirectResponse(url="/?error=Wrong password", status_code=302)

        sid = create_session(username)

        return RedirectResponse(url=f"/dashboard?sid={sid}", status_code=302)

    finally:
        db.close()

# =========================
# LOGOUT (NEW)
# =========================
@app.get("/logout")
def logout(sid: str):
    delete_session(sid)
    return RedirectResponse(url="/")

# =========================
# DASHBOARD (MODERN UI)
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):

    user = get_user(sid)

    if not user:
        return RedirectResponse(url="/")

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    files = os.listdir(user_dir)

    cards = ""
    for f in files:
        cards += f"""
        <div class="card">
            <div class="file">📄 {f}</div>

            <a href="/download/{user}/{f}">
                <button class="btn green">Download</button>
            </a>

            <a href="/delete/{user}/{f}?sid={sid}">
                <button class="btn red">Delete</button>
            </a>
        </div>
        """

    return f"""
    <html>
    <head>
        <style>
            body {{
                margin:0;
                font-family:Arial;
                background:#0f172a;
                color:white;
            }}

            .top {{
                background:#111827;
                padding:15px;
                display:flex;
                justify-content:space-between;
                align-items:center;
            }}

            .btn {{
                padding:8px 12px;
                border:none;
                border-radius:8px;
                cursor:pointer;
                color:white;
            }}

            .logout {{
                background:#ef4444;
            }}

            .back {{
                background:#6b7280;
            }}

            .container {{
                padding:20px;
                text-align:center;
            }}

            .upload {{
                background:#1e293b;
                padding:20px;
                border-radius:12px;
                width:320px;
                margin:auto;
            }}

            .grid {{
                display:flex;
                flex-wrap:wrap;
                justify-content:center;
                margin-top:20px;
            }}

            .card {{
                background:#1e293b;
                width:220px;
                margin:10px;
                padding:15px;
                border-radius:10px;
            }}

            .file {{
                margin-bottom:10px;
            }}

            .green {{
                background:#22c55e;
                width:100%;
                margin-top:5px;
            }}

            .red {{
                background:#ef4444;
                width:100%;
                margin-top:5px;
            }}

            .uploadbtn {{
                background:#3b82f6;
                width:100%;
            }}
        </style>
    </head>

    <body>

        <div class="top">
            <div>👤 {user}</div>

            <div>
                <button class="btn back" onclick="history.back()">⬅ Back</button>
                <a href="/logout?sid={sid}">
                    <button class="btn logout">Logout</button>
                </a>
            </div>
        </div>

        <div class="container">

            <div class="upload">
                <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button class="btn uploadbtn">⬆ Upload</button>
                </form>
            </div>

            <div class="grid">
                {cards if cards else "<p>No files yet</p>"}
            </div>

        </div>

    </body>
    </html>
    """

# =========================
# UPLOAD
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = File(...)):

    user = get_user(sid)

    if not user:
        return RedirectResponse(url="/")

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    path = os.path.join(user_dir, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return RedirectResponse(url=f"/dashboard?sid={sid}", status_code=302)

# =========================
# DOWNLOAD
# =========================
@app.get("/download/{user}/{filename}")
def download(user: str, filename: str):

    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        return FileResponse(path)

    return {"error": "not found"}

# =========================
# DELETE
# =========================
@app.get("/delete/{user}/{filename}")
def delete(user: str, filename: str, sid: str):

    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        os.remove(path)

    return RedirectResponse(url=f"/dashboard?sid={sid}", status_code=302)
