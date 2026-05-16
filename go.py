from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# الصفحة الرئيسية (Layout جانبي)
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    files = os.listdir(UPLOAD_DIR)

    file_items = ""
    for f in files:
        file_items += f"""
        <div class="file">
            📄 {f}
            <a href="/download/{f}">⬇</a>
            <a href="/delete/{f}">🗑</a>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>File Manager</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial;
                display: flex;
                height: 100vh;
            }}

            /* Sidebar left */
            .left {{
                width: 40%;
                background: #1e293b;
                color: white;
                padding: 20px;
                overflow-y: auto;
            }}

            /* Sidebar right */
            .right {{
                width: 60%;
                background: #f1f5f9;
                padding: 20px;
            }}

            h2 {{
                margin-top: 0;
            }}

            .file {{
                background: #334155;
                padding: 10px;
                margin: 10px 0;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
            }}

            .file a {{
                color: white;
                margin-left: 10px;
                text-decoration: none;
            }}

            .upload-box {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}

            button {{
                padding: 10px;
                margin-top: 10px;
                width: 100%;
                border: none;
                background: #2563eb;
                color: white;
                cursor: pointer;
            }}

            input {{
                width: 100%;
            }}
        </style>
    </head>

    <body>

        <!-- الملفات -->
        <div class="left">
            <h2>📁 Files</h2>
            {file_items if file_items else "<p>No files yet</p>"}
        </div>

        <!-- رفع الملفات -->
        <div class="right">
            <h2>⬆ Upload File</h2>

            <div class="upload-box">
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button type="submit">Upload</button>
                </form>
            </div>

        </div>

    </body>
    </html>
    """

# =========================
# رفع ملف
# =========================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "uploaded", "filename": file.filename}

# =========================
# تحميل ملف
# =========================
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        return FileResponse(file_path)

    return {"error": "not found"}

# =========================
# حذف ملف
# =========================
@app.get("/delete/{filename}")
def delete_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": "deleted"}
