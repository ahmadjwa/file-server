from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import os
import shutil
import random

app = FastAPI()

# =========================
# قاعدة البيانات
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# =========================
# جدول المستخدمين
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# =========================
# الملفات
# =========================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

sessions = {}

# =========================
# جلسات
# =========================
def create_session(user):
    sid = str(random.randint(100000, 999999))
    sessions[sid] = user
    return sid


def get_user(sid):
    return sessions.get(sid)

# =========================
# الصفحة الرئيسية
# =========================
@app.get("/", response_class=HTMLResponse)
def home(error: str = ""):

    error_html = ""
    if error:
        error_html = f"<div style='color:red;margin-bottom:10px'>{error}</div>"

    return f"""
    <html>
    <head>
        <title>Cloud Drive</title>
        <style>
            body {{
                margin:0;
                font-family:Arial;
                background:#0f172a;
                color:white;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }}

            .box {{
                background:#1e293b;
                padding:30px;
                border-radius:12px;
                width:350px;
                box-shadow:0 10px 30px rgba(0,0,0,0.4);
            }}

            input {{
                width:100%;
                padding:10px;
                margin:5px 0;
                border:none;
                border-radius:6px;
            }}

            button {{
                width:100%;
                padding:10px;
                background:#3b82f6;
                color:white;
                border:none;
                border-radius:6px;
                margin-top:10px;
                cursor:pointer;
            }}

            button:hover {{
                background:#2563eb;
            }}

            hr {{ opacity:0.3; }}
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

            <hr>

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
# Register
# =========================
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):

    db = SessionLocal()

    existing = db.query(User).filter(User.username == username).first()

    if existing:
        return RedirectResponse(url='/?error=Username already exists', status_code=302)

    hashed_password = bcrypt.hash(password)

    user = User(
        username=username,
        password=hashed_password
    )

    db.add(user)
    db.commit()

    return RedirectResponse(url='/?error=Account created successfully', status_code=302)

# =========================
# Login
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()

    if not user:
        return RedirectResponse(url='/?error=User not found', status_code=302)

    if not bcrypt.verify(password, user.password):
        return RedirectResponse(url='/?error=Wrong password', status_code=302)

    sid = create_session(username)

    return RedirectResponse(url=f'/dashboard?sid={sid}', status_code=302)

# =========================
# Dashboard
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):

    user = get_user(sid)

    if not user:
        return RedirectResponse(url='/')

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    files = os.listdir(user_dir)

    cards = ""

    for f in files:
        cards += f"""
        <div class='card'>
            <div>📄 {f}</div>

            <a href='/download/{user}/{f}'>
                <button class='download'>⬇ Download</button>
            </a>

            <a href='/delete/{user}/{f}?sid={sid}'>
                <button class='delete'>🗑 Delete</button>
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
                padding:20px;
                text-align:center;
                font-size:20px;
            }}

            .container {{
                padding:20px;
                text-align:center;
            }}

            .upload {{
                background:#1e293b;
                padding:20px;
                border-radius:12px;
                width:300px;
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

            button {{
                width:100%;
                padding:10px;
                margin-top:8px;
                border:none;
                border-radius:6px;
                color:white;
                cursor:pointer;
            }}

            .download {{ background:#22c55e; }}
            .delete {{ background:#ef4444; }}
            .uploadbtn {{ background:#3b82f6; }}
        </style>
    </head>

    <body>

        <div class='top'>👤 {user}</div>

        <div class='container'>

            <div class='upload'>
                <form action='/upload?sid={sid}' method='post' enctype='multipart/form-data'>
                    <input type='file' name='file' required>
                    <button class='uploadbtn'>⬆ Upload</button>
                </form>
            </div>

            <div class='grid'>
                {cards if cards else '<p>No files yet</p>'}
            </div>

        </div>

    </body>
    </html>
    """

# =========================
# Upload
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = File(...)):

    user = get_user(sid)

    if not user:
        return RedirectResponse(url='/')

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    path = os.path.join(user_dir, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return RedirectResponse(url=f'/dashboard?sid={sid}', status_code=302)

# =========================
# Download
# =========================
@app.get("/download/{user}/{filename}")
def download(user: str, filename: str):

    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        return FileResponse(path)

    return {"error": "not found"}

# =========================
# Delete
# =========================
@app.get("/delete/{user}/{filename}")
def delete(user: str, filename: str, sid: str):

    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        os.remove(path)

    return RedirectResponse(url=f'/dashboard?sid={sid}', status_code=302)
