from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import os
import shutil
import random

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

users = {}
sessions = {}

# =========================
# جلسة بسيطة
# =========================
def create_session(user):
    sid = str(random.randint(100000, 999999))
    sessions[sid] = user
    return sid

def get_user(sid):
    return sessions.get(sid)

# =========================
# الصفحة الرئيسية (تصميم احترافي)
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
    <title>Cloud Drive</title>
    <style>
        body {
            margin:0;
            font-family: Arial;
            background: linear-gradient(120deg,#0f172a,#1e293b);
            color:white;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
        }

        .box {
            background: rgba(255,255,255,0.08);
            padding:30px;
            border-radius:15px;
            width:350px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }

        input {
            width:100%;
            padding:12px;
            margin:8px 0;
            border:none;
            border-radius:8px;
            outline:none;
        }

        button {
            width:100%;
            padding:12px;
            margin-top:10px;
            border:none;
            border-radius:8px;
            background:#3b82f6;
            color:white;
            cursor:pointer;
            font-weight:bold;
        }

        button:hover {
            background:#2563eb;
        }

        h2,h3 {
            text-align:center;
        }

        .divider {
            text-align:center;
            margin:10px 0;
            opacity:0.6;
        }
    </style>
    </head>

    <body>
        <div class="box">

            <h2>☁ Cloud Drive</h2>

            <h3>Login</h3>
            <form action="/login" method="post">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>

            <div class="divider">OR</div>

            <h3>Register</h3>
            <form action="/register" method="post">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button type="submit">Create Account</button>
            </form>

        </div>
    </body>
    </html>
    """

# =========================
# تسجيل
# =========================
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    users[username] = password
    return RedirectResponse("/", status_code=302)

# =========================
# دخول
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if users.get(username) != password:
        return {"error": "wrong password"}

    sid = create_session(username)
    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# لوحة المستخدم
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):
    user = get_user(sid)
    if not user:
        return "Unauthorized"

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    files = os.listdir(user_dir)

    file_html = ""
    for f in files:
        file_html += f"""
        <div style='padding:8px;background:#1e293b;margin:5px;border-radius:8px;'>
            📄 {f}
            <a href="/download/{user}/{f}" style="color:#38bdf8;">⬇</a>
        </div>
        """

    return f"""
    <html>
    <head>
    <style>
        body {{
            margin:0;
            font-family: Arial;
            background:#0f172a;
            color:white;
        }}

        .top {{
            background:#111827;
            padding:15px;
            text-align:center;
            font-size:20px;
        }}

        .container {{
            display:flex;
            gap:20px;
            padding:20px;
        }}

        .left, .right {{
            flex:1;
            background:#1e293b;
            padding:20px;
            border-radius:12px;
        }}

        input {{
            width:100%;
            padding:10px;
        }}

        button {{
            padding:10px;
            width:100%;
            margin-top:10px;
            background:#3b82f6;
            border:none;
            color:white;
            border-radius:8px;
            cursor:pointer;
        }}
    </style>
    </head>

    <body>

        <div class="top">👤 Welcome {user}</div>

        <div class="container">

            <div class="left">
                <h3>⬆ Upload File</h3>
                <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button>Upload</button>
                </form>
            </div>

            <div class="right">
                <h3>📁 Your Files</h3>
                {file_html if file_html else "<p>No files</p>"}
            </div>

        </div>

    </body>
    </html>
    """

# =========================
# رفع
# =========================
@app.post("/upload")
def upload(sid: str, file: UploadFile = File(...)):
    user = get_user(sid)
    if not user:
        return {"error": "unauthorized"}

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    path = os.path.join(user_dir, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return RedirectResponse(f"/dashboard?sid={sid}", status_code=302)

# =========================
# تحميل
# =========================
@app.get("/download/{user}/{filename}")
def download(user: str, filename: str):
    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        return FileResponse(path)

    return {"error": "not found"}
