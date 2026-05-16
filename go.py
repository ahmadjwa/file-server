from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =====================
# واجهة الموقع (Frontend)
# =====================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Cloud File Server</title>
        <style>
            body { font-family: Arial; text-align: center; background:#f4f4f4; }
            .box { background:white; padding:20px; margin:50px auto; width:300px; border-radius:10px; }
            input, button { margin:10px; padding:10px; width:90%; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>📁 File Upload System</h2>
            
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <button type="submit">⬆️ Upload</button>
            </form>

            <br>
            <a href="/files">📂 View Files (JSON)</a>
        </div>
    </body>
    </html>
    """

# =====================
# رفع الملفات
# =====================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "uploaded", "filename": file.filename}

# =====================
# عرض الملفات
# =====================
@app.get("/files")
def list_files():
    return os.listdir(UPLOAD_DIR)

# =====================
# تحميل الملفات
# =====================
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        return FileResponse(file_path)

    return {"error": "not found"}
