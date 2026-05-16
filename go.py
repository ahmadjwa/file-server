from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader
import os
import random

app = FastAPI()

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# =========================
# DATABASE
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# =========================
# USER TABLE
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

# =========================
# FILE TABLE (NEW)
# =========================
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    filename = Column(String)
    url = Column(String)
    public_id = Column(String)

Base.metadata.create_all(bind=engine)

# =========================
# SESSION (simple)
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
# HOME
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Login / Register</h2>

    <form action="/login" method="post">
        <input name="username" placeholder="username">
        <input name="password" type="password">
        <button>Login</button>
    </form>

    <form action="/register" method="post">
        <input name="username" placeholder="username">
        <input name="password" type="password">
        <button>Register</button>
    </form>
    """

# =========================
# REGISTER
# =========================
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return RedirectResponse("/", status_code=302)

        hashed = pwd_context.hash(password)

        db.add(User(username=username, password=hashed))
        db.commit()

        return RedirectResponse("/", status_code=302)

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
            return RedirectResponse("/", status_code=302)

        if not pwd_context.verify(password, user.password):
            return RedirectResponse("/", status_code=302)

        sid = create_session(username)
        return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

    finally:
        db.close()

# =========================
# LOGOUT
# =========================
@app.get("/logout")
def logout(sid: str):
    delete_session(sid)
    return RedirectResponse("/", status_code=302)

# =========================
# DASHBOARD
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):

    user = get_user(sid)
    if not user:
        return RedirectResponse("/")

    db = SessionLocal()

    files = db.query(File).filter(File.username == user).all()

    cards = ""
    for f in files:
        cards += f"""
        <div>
            📄 {f.filename}<br>
            <a href="{f.url}" target="_blank">Download</a><br>
            <a href="/delete/{f.id}?sid={sid}">Delete</a>
        </div>
        <hr>
        """

    db.close()

    return f"""
    <h2>Welcome {user}</h2>

    <a href="/logout?sid={sid}">Logout</a>

    <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button>Upload</button>
    </form>

    <hr>

    {cards if cards else "No files"}
    """

# =========================
# UPLOAD TO CLOUDINARY
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = File(...)):

    user = get_user(sid)
    if not user:
        return RedirectResponse("/")

    db = SessionLocal()

    result = cloudinary.uploader.upload(
        file.file,
        folder=f"users/{user}"
    )

    db.add(File(
        username=user,
        filename=file.filename,
        url=result["secure_url"],
        public_id=result["public_id"]
    ))

    db.commit()
    db.close()

    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# DELETE FROM CLOUDINARY
# =========================
@app.get("/delete/{file_id}")
def delete(file_id: int, sid: str):

    db = SessionLocal()

    file = db.query(File).filter(File.id == file_id).first()

    if file:
        cloudinary.uploader.destroy(file.public_id)
        db.delete(file)
        db.commit()

    db.close()

    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)
