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

def delete_session(sid):
    if sid in sessions:
        del sessions[sid]

# =========================
# HOME PAGE
# =========================
@app.get("/", response_class=HTMLResponse)
def home(error: str = "", success: str = ""):

    # تحديد لون الرسالة حسب النوع
    message_html = ""
    
    if error:
        message_html = f"""
        <div class="message error-message">
            <span class="message-icon">❌</span>
            <span>{error}</span>
        </div>
        """
    elif success:
        message_html = f"""
        <div class="message success-message">
            <span class="message-icon">✅</span>
            <span>{success}</span>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Super Uploader | Cloud Storage</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                margin:0;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color:white;
                display:flex;
                justify-content:center;
                align-items:center;
                min-height:100vh;
                position: relative;
                overflow-x: hidden;
            }}
            
            body::before {{
                content: '';
                position: absolute;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
                background-size: 50px 50px;
                animation: moveBackground 20s linear infinite;
                pointer-events: none;
            }}
            
            @keyframes moveBackground {{
                0% {{
                    transform: translate(0, 0);
                }}
                100% {{
                    transform: translate(50px, 50px);
                }}
            }}

            .box {{
                background: rgba(17, 24, 39, 0.95);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 24px;
                width: 400px;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.2);
                animation: fadeInUp 0.6s ease-out;
                position: relative;
                z-index: 1;
            }}
            
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            .logo {{
                text-align: center;
                margin-bottom: 30px;
            }}
            
            .logo-icon {{
                font-size: 60px;
                margin-bottom: 10px;
                display: inline-block;
                animation: float 3s ease-in-out infinite;
            }}
            
            @keyframes float {{
                0%, 100% {{
                    transform: translateY(0);
                }}
                50% {{
                    transform: translateY(-10px);
                }}
            }}
            
            h2 {{
                text-align:center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                font-size: 28px;
                font-weight: 800;
                margin-top: 10px;
            }}
            
            .subtitle {{
                text-align: center;
                color: #9ca3af;
                font-size: 14px;
                margin-top: 5px;
            }}

            input {{
                width:100%;
                padding: 12px 16px;
                margin: 8px 0;
                border: 2px solid #374151;
                border-radius: 12px;
                background: #1f2937;
                color:white;
                font-size: 14px;
                transition: all 0.3s;
                font-family: 'Inter', sans-serif;
            }}
            
            input:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            
            input::placeholder {{
                color: #6b7280;
            }}

            button {{
                width:100%;
                padding: 12px;
                margin-top: 16px;
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color:white;
                cursor:pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s;
                font-family: 'Inter', sans-serif;
                position: relative;
                overflow: hidden;
            }}
            
            button::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255,255,255,0.3);
                transform: translate(-50%, -50%);
                transition: width 0.6s, height 0.6s;
            }}
            
            button:hover::before {{
                width: 300px;
                height: 300px;
            }}
            
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 25px -5px rgba(102, 126, 234, 0.4);
            }}
            
            button:active {{
                transform: translateY(0);
            }}

            hr {{
                border:0;
                height:1px;
                background: linear-gradient(90deg, transparent, #374151, transparent);
                margin: 25px 0;
            }}
            
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 15px;
                color: #e5e7eb;
            }}
            
            /* رسائل النجاح والفشل */
            .message {{
                padding: 12px 16px;
                border-radius: 12px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                animation: slideIn 0.5s ease-out;
            }}
            
            .success-message {{
                background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.2));
                border: 2px solid #22c55e;
                color: #4ade80;
                box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
            }}
            
            .error-message {{
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
                border: 2px solid #ef4444;
                color: #fca5a5;
                box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
            }}
            
            .message-icon {{
                font-size: 20px;
            }}
            
            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateX(-20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateX(0);
                }}
            }}
        </style>
    </head>

    <body>
        <div class="box">
            <div class="logo">
                <div class="logo-icon">🚀</div>
                <h2>Super Uploader</h2>
                <div class="subtitle">Your Premium Cloud Storage</div>
            </div>
            
            {message_html}

            <form action="/login" method="post">
                <div class="section-title">🔐 Login to your account</div>
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button>✨ Login ✨</button>
            </form>

            <hr>

            <form action="/register" method="post">
                <div class="section-title">🆕 Create new account</div>
                <input name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button>🚀 Sign Up 🚀</button>
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
            # فشل - اسم المستخدم موجود
            return RedirectResponse(url="/?error=Username already exists", status_code=302)

        hashed = pwd_context.hash(password)

        user = User(username=username, password=hashed)

        db.add(user)
        db.commit()

        # نجاح - تم إنشاء الحساب
        return RedirectResponse(url="/?success=Account created successfully! 🎉", status_code=302)

    except Exception as e:
        db.rollback()
        # فشل - خطأ في النظام
        return RedirectResponse(url=f"/?error=Registration failed: {str(e)}", status_code=302)

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
            # فشل - المستخدم غير موجود
            return RedirectResponse(url="/?error=User not found ❌", status_code=302)

        if not pwd_context.verify(password, user.password):
            # فشل - كلمة المرور خاطئة
            return RedirectResponse(url="/?error=Wrong password ❌", status_code=302)

        sid = create_session(username)
        
        # نجاح - تم تسجيل الدخول
        return RedirectResponse(url=f"/dashboard?sid={sid}", status_code=302)

    finally:
        db.close()

# =========================
# LOGOUT
# =========================
@app.get("/logout")
def logout(sid: str):
    delete_session(sid)
    # نجاح - تم تسجيل الخروج
    return RedirectResponse(url="/?success=Logged out successfully! 👋", status_code=302)

# =========================
# DASHBOARD (MODERN UI with Logout & Back buttons)
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
        # الحصول على حجم الملف
        file_path = os.path.join(user_dir, f)
        size_bytes = os.path.getsize(file_path)
        
        # تحويل الحجم إلى KB أو MB
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            
        cards += f"""
        <div class="card" data-filename="{f}">
            <div class="file-icon">📄</div>
            <div class="file-name">{f}</div>
            <div class="file-size">{size_str}</div>
            <div class="actions">
                <a class="btn download" href="/download/{user}/{f}">⬇️ Download</a>
                <a class="btn delete" href="/delete/{user}/{f}?sid={sid}">🗑️ Delete</a>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Dashboard | Super Uploader</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                margin:0;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color:white;
                min-height: 100vh;
            }}
            
            .navbar {{
                background: rgba(17, 24, 39, 0.95);
                backdrop-filter: blur(10px);
                padding: 18px 30px;
                display:flex;
                justify-content:space-between;
                align-items:center;
                box-shadow: 0 5px 20px rgba(0,0,0,0.3);
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            
            .logo-section {{
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .logo-icon {{
                font-size: 32px;
                animation: spin 10s linear infinite;
            }}
            
            @keyframes spin {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
            
            .navbar h2 {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                background-clip: text;
                color: transparent;
                font-size: 24px;
                font-weight: 800;
                margin:0;
            }}
            
            .nav-buttons {{
                display:flex;
                gap: 12px;
                align-items:center;
            }}
            
            .user-info {{
                display: flex;
                align-items: center;
                gap: 10px;
                background: rgba(102, 126, 234, 0.2);
                padding: 8px 16px;
                border-radius: 12px;
                border: 1px solid rgba(102, 126, 234, 0.3);
            }}
            
            .username {{
                color: #e5e7eb;
                font-weight: 500;
            }}
            
            .nav-btn {{
                padding: 8px 20px;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
                font-family: 'Inter', sans-serif;
                display: inline-block;
            }}
            
            .back-btn {{
                background: rgba(75, 85, 99, 0.9);
                color: white;
            }}
            
            .back-btn:hover {{
                background: #4b5563;
                transform: translateY(-2px);
            }}
            
            .logout-btn {{
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
            }}
            
            .logout-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(239, 68, 68, 0.3);
            }}
            
            .container {{
                max-width: 1200px;
                margin: auto;
                padding: 30px;
            }}
            
            .upload-box {{
                background: rgba(17, 24, 39, 0.95);
                backdrop-filter: blur(10px);
                padding: 25px;
                border-radius: 20px;
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s;
            }}
            
            .upload-box:hover {{
                transform: translateY(-5px);
                box-shadow: 0 20px 40px -15px rgba(0,0,0,0.3);
            }}
            
            .upload-title {{
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            input[type=file] {{
                color: white;
                padding: 10px;
                background: #1f2937;
                border-radius: 12px;
                border: 2px solid #374151;
                cursor: pointer;
            }}
            
            input[type=file]::file-selector-button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-weight: 600;
                margin-right: 10px;
            }}
            
            button {{
                padding: 12px 24px;
                border: none;
                border-radius: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                cursor: pointer;
                font-weight: 600;
                font-size: 14px;
                transition: all 0.3s;
                font-family: 'Inter', sans-serif;
                margin-left: 10px;
            }}
            
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 25px -5px rgba(102, 126, 234, 0.4);
            }}
            
            .stats {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            
            .file-count {{
                background: rgba(102, 126, 234, 0.2);
                padding: 8px 16px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 500;
            }}
            
            .grid {{
                display:grid;
                grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
                gap: 20px;
            }}
            
            .card {{
                background: rgba(17, 24, 39, 0.95);
                backdrop-filter: blur(10px);
                padding: 20px;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s;
                animation: fadeInUp 0.5s ease-out;
            }}
            
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .card:hover {{
                transform: translateY(-8px) scale(1.02);
                border-color: #667eea;
                box-shadow: 0 20px 40px -15px rgba(102, 126, 234, 0.3);
            }}
            
            .file-icon {{
                font-size: 48px;
                text-align: center;
                margin-bottom: 10px;
            }}
            
            .file-name {{
                font-weight: 600;
                margin-bottom: 5px;
                word-break: break-word;
                color: #e5e7eb;
                text-align: center;
                font-size: 16px;
            }}
            
            .file-size {{
                font-size: 12px;
                color: #9ca3af;
                text-align: center;
                margin-bottom: 15px;
            }}
            
            .actions {{
                display:flex;
                gap: 10px;
            }}
            
            .btn {{
                flex:1;
                text-align:center;
                padding: 10px;
                border-radius: 10px;
                text-decoration:none;
                font-size: 13px;
                font-weight: 600;
                transition: all 0.3s;
            }}
            
            .download {{
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                color:white;
            }}
            
            .download:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(34, 197, 94, 0.3);
            }}
            
            .delete {{
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color:white;
            }}
            
            .delete:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(239, 68, 68, 0.3);
            }}
            
            .empty {{
                text-align: center;
                padding: 60px;
                background: rgba(17, 24, 39, 0.5);
                border-radius: 20px;
                color: #9ca3af;
                font-size: 18px;
                grid-column: 1 / -1;
            }}
        </style>
        <script>
            function goBack() {{
                window.history.back();
            }}
        </script>
    </head>

    <body>
        <div class="navbar">
            <div class="logo-section">
                <div class="logo-icon">🚀</div>
                <h2>Super Uploader</h2>
            </div>
            <div class="nav-buttons">
                <div class="user-info">
                    <span>👤</span>
                    <span class="username">{user}</span>
                </div>
                <button onclick="goBack()" class="nav-btn back-btn">← Back</button>
                <a href="/logout?sid={sid}" class="nav-btn logout-btn">🚪 Logout</a>
            </div>
        </div>

        <div class="container">
            <div class="upload-box">
                <div class="upload-title">
                    <span>📤</span>
                    <span>Upload New File</span>
                </div>
                <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button>⬆️ Upload Now</button>
                </form>
            </div>
            
            <div class="stats">
                <div class="file-count">
                    📁 Total Files: {len(files)}
                </div>
            </div>

            <div class="grid">
                {cards if cards else "<div class='empty'>✨ No files uploaded yet<br>Click the upload button to get started! ✨</div>"}
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
