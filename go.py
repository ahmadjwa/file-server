from fastapi import FastAPI, UploadFile, File as FastAPIFile, Form
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
# DATABASE (FIXED FOR RENDER)
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

# مهم جدًا لـ Render PostgreSQL
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg2://",
        1
    )

connect_args = {}

if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# =========================
# PASSWORD SECURITY
# =========================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =========================
# MODELS
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    name = Column(String)
    url = Column(String)
    public_id = Column(String)

Base.metadata.create_all(bind=engine)

# =========================
# SESSIONS (TEMP MEMORY)
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
# HOME PAGE
# =========================
@app.get("/", response_class=HTMLResponse)
def home(error: str = "", success: str = ""):

    msg = ""

    if error:
        msg = f"<p style='color:red'>{error}</p>"
    elif success:
        msg = f"<p style='color:lime'>{success}</p>"

    return f"""
    <html>
    <body style="font-family:Arial;background:#111;color:white;text-align:center;padding:50px">

        <h1>🚀 Super Uploader</h1>

        {msg}

        <form action="/login" method="post">
            <h3>Login</h3>
            <input name="username" placeholder="username"><br>
            <input type="password" name="password"><br>
            <button>Login</button>
        </form>

        <hr>

        <form action="/register" method="post">
            <h3>Register</h3>
            <input name="username" placeholder="username"><br>
            <input type="password" name="password"><br>
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

        db.add(User(
            username=username,
            password=pwd_context.hash(password)
        ))
        db.commit()

        return RedirectResponse("/?success=Account created", status_code=302)

    finally:
        db.close()

# =========================
# LOGIN (FIXED SECURITY CHECK)
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return RedirectResponse("/?error=User not found", status_code=302)

        # FIX: safe password verify
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

    db = SessionLocal()
    try:
        files = db.query(File).filter(File.username == user).all()
    finally:
        db.close()

    cards = ""

    for f in files:
        cards += f"""
        <div style="border:1px solid #444;padding:10px;margin:10px">
            <p>📄 {f.name}</p>
            <a href="{f.url}" target="_blank">Download</a>
            <a href="/delete-cloud/{sid}/{f.public_id}">Delete</a>
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
# UPLOAD (CLOUDINARY + DB)
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = FastAPIFile(...)):

    user = get_user(sid)

    if not user:
        return RedirectResponse("/")

    result = cloudinary.uploader.upload(
        file.file,
        folder=f"super_uploader/{user}",
        resource_type="auto"
    )

    db = SessionLocal()
    try:
        db.add(File(
            username=user,
            name=file.filename,
            url=result["secure_url"],
            public_id=result["public_id"]
        ))
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# DELETE
# =========================
@app.get("/delete-cloud/{sid}/{public_id}")
def delete_cloud(sid: str, public_id: str):

    cloudinary.uploader.destroy(public_id)

    db = SessionLocal()
    try:
        db.query(File).filter(File.public_id == public_id).delete()
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f"/dashboard?sid={sid}")

# =========================
# LOGOUT
# =========================
@app.get("/logout")
def logout(sid: str):
    delete_session(sid)
    return RedirectResponse("/?success=Logged out")
