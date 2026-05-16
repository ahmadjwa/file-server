from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# قاعدة بيانات بسيطة (داخل الذاكرة)
# =========================
users = {}  # username -> password
sessions = {}  # session_id -> username

# =========================
# توليد Session بسيط
# =========================
def create_session(username):
    import random
    sid = str(random.randint(100000, 999999))
    sessions[sid] = username
    return sid

def get_user(session_id):
    return sessions.get(session_id)

# =========================
# الصفحة الرئيسية (تسجيل دخول)
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>🔐 Login</h2>
    <form action="/login" method="post">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>

    <br>

    <h3>🆕 Register</h3>
    <form action="/register" method="post">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Register</button>
    </form>
    """

# =========================
# تسجيل حساب جديد
# =========================
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    if username in users:
        return {"error": "User already exists"}

    users[username] = password
    return RedirectResponse(url="/", status_code=302)

# =========================
# تسجيل الدخول
# =========================
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if users.get(username) != password:
        return {"error": "Wrong credentials"}

    sid = create_session(username)
    return RedirectResponse(url=f"/dashboard?sid={sid}", status_code=302)

# =========================
# لوحة المستخدم
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):
    user = get_user(sid)
    if not user:
        return "Unauthorized"

    user_folder = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_folder, exist_ok=True)

    files = os.listdir(user_folder)

    file_list = ""
    for f in files:
        file_list += f"""
        <li>
            📄 {f}
            <a href="/download/{user}/{f}">⬇ Download</a>
        </li>
        """

    return f"""
    <h2>👤 Welcome {user}</h2>

    <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Upload</button>
    </form>

    <h3>📁 Your Files</h3>
    <ul>{file_list if file_list else "<p>No files</p>"}</ul>
    """

# =========================
# رفع ملف (خاص بالمستخدم)
# =========================
@app.post("/upload")
def upload_file(sid: str, file: UploadFile = File(...)):
    user = get_user(sid)
    if not user:
        return {"error": "Unauthorized"}

    user_folder = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return RedirectResponse(url=f"/dashboard?sid={sid}", status_code=302)

# =========================
# تحميل ملف (خاص بالمستخدم)
# =========================
@app.get("/download/{user}/{filename}")
def download(user: str, filename: str):
    file_path = os.path.join(UPLOAD_DIR, user, filename)

    if os.path.exists(file_path):
        return FileResponse(file_path)

    return {"error": "not found"}
