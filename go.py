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

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

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
# FILES
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

# =========================
# HOME PAGE
# =========================
@app.get("/", response_class=HTMLResponse)
def home(error: str = ""):

    error_html = f"<div style='color:#f87171;margin-bottom:10px'>{error}</div>" if error else ""

    return f"""
    <html>
    <head>
        <title>Cloud Drive</title>
        <style>
            body {{
                margin:0;
                font-family:Arial;
                background: linear-gradient(135deg,#0f172a,#1e293b);
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
                width:350px;
                box-shadow:0 10px 40px rgba(0,0,0,0.5);
            }}

            h2 {{
                text-align:center;
                color:#60a5fa;
            }}

            input {{
                width:100%;
                padding:10px;
                margin:6px 0;
                border:none;
                border-radius:8px;
                background:#1f2937;
                color:white;
            }}

            button {{
                width:100%;
                padding:10px;
                margin-top:10px;
                border:none;
                border-radius:8px;
                background:#3b82f6;
                color:white;
                cursor:pointer;
            }}

            button:hover {{
                background:#2563eb;
            }}

            hr {{
                border:0;
                height:1px;
                background:#374151;
                margin:15px 0;
            }}
        </style>
    </head>

    <body>

        <div class="box">

            <h2>☁ Cloud Drive</h2>
            {error_html}

            <form action="/login" method="post">
                <h3>Login</h3>
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button>Login</button>
            </form>

            <hr>

            <form action="/register" method="post">
                <h3>Register</h3>
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
        password = password.strip()

        existing = db.query(User).filter(User.username == username).first()

        if existing:
            return RedirectResponse(url="/?error=Username already exists", status_code=302)

        hashed = pwd_context.hash(password)

        user = User(username=username, password=hashed)

        db.add(user)
        db.commit()

        return RedirectResponse(url="/?error=Account created successfully", status_code=302)

    except Exception as e:
        db.rollback()
        return HTMLResponse(f"<h1>Error</h1><pre>{e}</pre>")

    finally:
        db.close()

# =========================
# LOGIN
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    db = SessionLocal()
    try:
        password = password.strip()

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

            <div class="actions">
                <a class="btn download" href="/download/{user}/{f}">Download</a>
                <a class="btn delete" href="/delete/{user}/{f}?sid={sid}">Delete</a>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Dashboard</title>
        <style>

            body {{
                margin:0;
                font-family:Arial;
                background:#0b1220;
                color:white;
            }}

            .navbar {{
                background:#111827;
                padding:15px 25px;
                display:flex;
                justify-content:space-between;
                align-items:center;
                box-shadow:0 5px 20px rgba(0,0,0,0.4);
            }}

            .navbar h2 {{
                color:#60a5fa;
                margin:0;
            }}

            .container {{
                max-width:1000px;
                margin:auto;
                padding:25px;
            }}

            .upload-box {{
                background:#111827;
                padding:15px;
                border-radius:12px;
                margin-bottom:20px;
            }}

            input[type=file] {{
                color:white;
            }}

            button {{
                padding:10px 15px;
                border:none;
                border-radius:8px;
                background:#3b82f6;
                color:white;
                cursor:pointer;
            }}

            .grid {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                gap:15px;
            }}

            .card {{
                background:#111827;
                padding:15px;
                border-radius:12px;
                border:1px solid #1f2937;
                transition:0.3s;
            }}

            .card:hover {{
                transform:translateY(-5px);
                border-color:#3b82f6;
            }}

            .file {{
                margin-bottom:10px;
                word-break:break-word;
                color:#e5e7eb;
            }}

            .actions {{
                display:flex;
                gap:8px;
            }}

            .btn {{
                flex:1;
                text-align:center;
                padding:8px;
                border-radius:6px;
                text-decoration:none;
                font-size:13px;
            }}

            .download {{
                background:#22c55e;
                color:white;
            }}

            .delete {{
                background:#ef4444;
                color:white;
            }}

            .empty {{
                text-align:center;
                color:#94a3b8;
                margin-top:30px;
            }}

        </style>
    </head>

    <body>

        <div class="navbar">
            <h2>☁ Cloud Drive</h2>
            <div>👤 {user}</div>
        </div>

        <div class="container">

            <div class="upload-box">
                <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button>Upload</button>
                </form>
            </div>

            <div class="grid">
                {cards if cards else "<div class='empty'>No files uploaded yet</div>"}
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
