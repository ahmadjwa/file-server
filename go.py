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
# Dashboard احترافي
# =========================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(sid: str):
    user = get_user(sid)
    if not user:
        return "Unauthorized"

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    files = os.listdir(user_dir)

    cards = ""
    for f in files:
        cards += f"""
        <div class="card">
            <div class="name">📄 {f}</div>

            <div class="buttons">
                <a href="/download/{user}/{f}">
                    <button class="download">⬇ Download</button>
                </a>

                <a href="/delete/{user}/{f}?sid={sid}">
                    <button class="delete">🗑 Delete</button>
                </a>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
    <style>
        body {{
            margin:0;
            font-family: Arial;
            background: #0f172a;
            color:white;
        }}

        .top {{
            padding:20px;
            text-align:center;
            background:#111827;
            font-size:20px;
        }}

        .container {{
            padding:20px;
            text-align:center;
        }}

        .upload-box {{
            background:#1e293b;
            padding:20px;
            border-radius:12px;
            width:300px;
            margin:auto;
        }}

        input {{
            width:100%;
            padding:10px;
            margin-top:10px;
        }}

        button {{
            width:100%;
            padding:10px;
            margin-top:10px;
            border:none;
            border-radius:8px;
            cursor:pointer;
        }}

        .upload-btn {{
            background:#3b82f6;
            color:white;
        }}

        .grid {{
            display:flex;
            flex-wrap:wrap;
            justify-content:center;
            margin-top:20px;
        }}

        .card {{
            background:#1e293b;
            margin:10px;
            padding:15px;
            border-radius:12px;
            width:220px;
        }}

        .name {{
            margin-bottom:10px;
        }}

        .buttons button {{
            margin-top:5px;
        }}

        .download {{
            background:#22c55e;
            color:white;
        }}

        .delete {{
            background:#ef4444;
            color:white;
        }}
    </style>
    </head>

    <body>

        <div class="top">👤 Dashboard - {user}</div>

        <div class="container">

            <div class="upload-box">
                <form action="/upload?sid={sid}" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button class="upload-btn">⬆ Upload File</button>
                </form>
            </div>

            <div class="grid">
                {cards if cards else "<p>No files yet</p>"}
            </div>

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
        return {"error": "unauthorized"}

    user_dir = os.path.join(UPLOAD_DIR, user)
    os.makedirs(user_dir, exist_ok=True)

    path = os.path.join(user_dir, file.filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return f"""
    <script>
        alert('Uploaded successfully ✔');
        window.location.href='/dashboard?sid={sid}';
    </script>
    """

# =========================
# تحميل
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

    return f"""
    <script>
        alert('Deleted ✔');
        window.location.href='/dashboard?sid={sid}';
    </script>
    """
