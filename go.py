from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
import os
import shutil
import random

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

users = {}
sessions = {}

def create_session(user):
    sid = str(random.randint(100000, 999999))
    sessions[sid] = user
    return sid

def get_user(sid):
    return sessions.get(sid)

# =========================
# صفحة الدخول مع رسائل
# =========================
@app.get("/", response_class=HTMLResponse)
def home(msg: str = "", error: str = ""):

    msg_html = ""
    if msg:
        msg_html = f"<div style='color:green;margin-bottom:10px;'>✅ {msg}</div>"
    if error:
        msg_html = f"<div style='color:red;margin-bottom:10px;'>❌ {error}</div>"

    return f"""
    <html>
    <head>
    <style>
        body {{
            font-family: Arial;
            background: #0f172a;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
            color:white;
        }}
        .box {{
            background:#1e293b;
            padding:25px;
            border-radius:12px;
            width:320px;
            text-align:center;
        }}
        input {{
            width:100%;
            padding:10px;
            margin:5px 0;
        }}
        button {{
            width:100%;
            padding:10px;
            background:#3b82f6;
            border:none;
            color:white;
            margin-top:10px;
            cursor:pointer;
        }}
    </style>
    </head>

    <body>
        <div class="box">
            <h2>🔐 Login System</h2>

            {msg_html}

            <form action="/login" method="post">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Login</button>
            </form>

            <hr>

            <form action="/register" method="post">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Register</button>
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
    return HTMLResponse("""
        <script>
            window.location.href='/?msg=Account created successfully';
        </script>
    """)

# =========================
# دخول (مع رسالة خطأ أو نجاح)
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    if users.get(username) != password:
        return HTMLResponse("""
            <script>
                window.location.href='/?error=Wrong username or password';
            </script>
        """)

    sid = create_session(username)

    return HTMLResponse(f"""
        <script>
            alert('Login successful ✔');
            window.location.href='/dashboard?sid={sid}';
        </script>
    """)

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
        <div>📄 {f} - <a href="/download/{user}/{f}">⬇</a></div>
        """

    return f"""
    <h2>👤 Welcome {user}</h2>

    <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button>Upload</button>
    </form>

    <hr>

    {file_html if file_html else "<p>No files</p>"}
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

    return HTMLResponse(f"""
        <script>
            alert('File uploaded successfully ✔');
            window.location.href='/dashboard?sid={sid}';
        </script>
    """)

# =========================
# تحميل
# =========================
@app.get("/download/{user}/{filename}")
def download(user: str, filename: str):
    path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(path):
        return FileResponse(path)

    return {"error": "not found"}
