from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
import os
import random

import cloudinary
import cloudinary.uploader

app = FastAPI()

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# =========================
# DATABASE
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///./test.db"

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# =========================
# USER MODEL
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# =========================
# SESSIONS (temporary memory)
# =========================
sessions = {}

def create_session(user):
    sid = str(random.randint(100000, 999999))
    sessions[sid] = user
    return sid

def get_user(sid):
    return sessions.get(sid)

def delete_session(sid):
    sessions.pop(sid, None)

# =========================
# CLOUD FILE STORAGE (in memory index)
# =========================
# sessions["files"] = { user: [ {name,url,public_id} ] }
sessions["files"] = {}

# =========================
# HOME PAGE
# =========================
@app.get("/", response_class=HTMLResponse)
def home(error: str = "", success: str = ""):

    message_html = ""

    if error:
        message_html = f"<div style='color:red'>{error}</div>"
    elif success:
        message_html = f"<div style='color:lime'>{success}</div>"

    return f"""
    <html>
    <body style="font-family:Arial;background:#111;color:white;text-align:center;padding:50px">

        <h1>🚀 Super Uploader</h1>

        {message_html}

        <form action="/login" method="post">
            <h3>Login</h3>
            <input name="username" placeholder="username"><br>
            <input type="password" name="password" placeholder="password"><br>
            <button>Login</button>
        </form>

        <hr>

        <form action="/register" method="post">
            <h3>Register</h3>
            <input name="username" placeholder="username"><br>
            <input type="password" name="password" placeholder="password"><br>
            <button>Register</button>
        </form>

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
            return RedirectResponse("/?error=User exists", status_code=302)

        hashed = pwd_context.hash(password)
        db.add(User(username=username, password=hashed))
        db.commit()

        return RedirectResponse("/?success=Account created", status_code=302)

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
            return RedirectResponse("/?error=User not found", status_code=302)

        if not pwd_context.verify(password, user.password):
            return RedirectResponse("/?error=Wrong password", status_code=302)

        sid = create_session(username)

        return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

    finally:
        db.close()

# =========================
# DASHBOARD
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):

    user = get_user(sid)

    if not user:
        return RedirectResponse("/")

    files = sessions["files"].get(user, [])

    cards = ""

    for f in files:
        cards += f"""
        <div style="border:1px solid #444;padding:10px;margin:10px">
            <p>📄 {f['name']}</p>
            <a href="{f['url']}" target="_blank">Download</a>
            <a href="/delete-cloud/{sid}/{f['public_id']}">Delete</a>
        </div>
        """

    return f"""
    <html>
    <body style="background:#111;color:white;text-align:center">

        <h2>Welcome {user}</h2>

        <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <button>Upload</button>
        </form>

        <h3>Your Files</h3>

        {cards if cards else "No files yet"}

        <br><br>
        <a href="/logout?sid={sid}">Logout</a>

    </body>
    </html>
    """

# =========================
# UPLOAD (CLOUDINARY)
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = File(...)):

    user = get_user(sid)

    if not user:
        return RedirectResponse("/")

    result = cloudinary.uploader.upload(
        file.file,
        folder=f"super_uploader/{user}",
        resource_type="auto"
    )

    sessions["files"].setdefault(user, []).append({
        "name": file.filename,
        "url": result["secure_url"],
        "public_id": result["public_id"]
    })

    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# DELETE (CLOUDINARY)
# =========================
@app.get("/delete-cloud/{sid}/{public_id}")
def delete_cloud(sid: str, public_id: str):

    cloudinary.uploader.destroy(public_id)

    user = get_user(sid)

    if user and user in sessions["files"]:
        sessions["files"][user] = [
            f for f in sessions["files"][user]
            if f["public_id"] != public_id
        ]

    return RedirectResponse(f"/dashboard?sid={sid}")

# =========================
# LOGOUT
# =========================
@app.get("/logout")
def logout(sid: str):
    delete_session(sid)
    return RedirectResponse("/?success=Logged out")
