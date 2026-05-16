from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
import os
import shutil
import random

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

users = {}
sessions = {}

# =========================
# إنشاء جلسة
# =========================
def create_session(user):
    sid = str(random.randint(100000, 999999))
    sessions[sid] = user
    return sid

def get_user(sid):
    return sessions.get(sid)

# =========================
# 🔥 الصفحة الرئيسية (تم إصلاح Not Found)
# =========================
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
    <head>
        <title>Cloud Drive</title>
        <style>
            body{
                margin:0;
                font-family:Arial;
                background:#0f172a;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
                color:white;
            }
            .box{
                background:#1e293b;
                padding:25px;
                border-radius:12px;
                width:320px;
                text-align:center;
                box-shadow:0 10px 30px rgba(0,0,0,0.4);
            }
            input{
                width:100%;
                padding:10px;
                margin:5px 0;
                border-radius:6px;
                border:none;
            }
            button{
                width:100%;
                padding:10px;
                margin-top:10px;
                border:none;
                border-radius:6px;
                background:#3b82f6;
                color:white;
                cursor:pointer;
            }
            button:hover{
                background:#2563eb;
            }
            hr{opacity:0.3}
        </style>
    </head>

    <body>
        <div class="box">
            <h2>☁ Cloud Drive</h2>

            <h3>Login</h3>
            <form action="/login" method="post">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Login</button>
            </form>

            <hr>

            <h3>Register</h3>
            <form action="/register" method="post">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" required>
                <button>Create Account</button>
            </form>
        </div>
    </body>
    </html>
    """

# =========================
# تسجيل حساب
# =========================
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    users[username] = password
    return RedirectResponse("/", status_code=302)

# =========================
# تسجيل دخول
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if users.get(username) != password:
        return HTMLResponse("""
            <script>
                alert('Wrong username or password');
                window.location.href='/';
            </script>
        """)

    sid = create_session(username)
    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# داشبورد احترافي
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):
    user = get_user(sid)
    if not user:
        return RedirectResponse("/")

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    files = os.listdir(user_dir)

    cards = ""
    for f in files:
        cards += f"""
        <div style="background:#1e293b;padding:10px;margin:10px;border-radius:10px;">
            📄 {f}<br><br>
            <a href="/download/{user}/{f}">
                <button style="background:#22c55e;color:white;">⬇ Download</button>
            </a>

            <a href="/delete/{user}/{f}?sid={sid}">
                <button style="background:#ef4444;color:white;">🗑 Delete</button>
            </a>
        </div>
        """

    return f"""
    <html>
    <body style="background:#0f172a;color:white;font-family:Arial;">
        <div style="text-align:center;padding:15px;background:#111827;">
            👤 Welcome {user}
        </div>

        <div style="text-align:center;margin-top:20px;">
            <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button style="padding:10px;background:#3b82f6;color:white;border:none;border-radius:6px;">
                    Upload
                </button>
            </form>
        </div>

        <div style="display:flex;flex-wrap:wrap;justify-content:center;">
            {cards if cards else "<p>No files yet</p>"}
        </div>
    </body>
    </html>
    """

# =========================
# رفع ملف
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = File(...)):
    user = get_user(sid)
    if not user:
        return RedirectResponse("/")

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    path = os.path.join(user_dir, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# تحميل ملف
# =========================
@app.get("/download/{user}/{filename}")
def download(user: str, filename: str):
    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        return FileResponse(path)

    return {"error": "not found"}

# =========================
# حذف ملف
# =========================
@app.get("/delete/{user}/{filename}")
def delete(user: str, filename: str, sid: str):
    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        os.remove(path)

    return RedirectResponse(f"/dashboard?sid={sid}")
