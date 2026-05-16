from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ======================
# الصفحة الرئيسية
# ======================
@app.get("/", response_class=HTMLResponse)
def home():
    files = os.listdir(UPLOAD_DIR)

    file_list_html = ""
    for f in files:
        file_list_html += f"""
        <li>
            {f} 
            <a href="/download/{f}">
                <button>⬇ Download</button>
            </a>
        </li>
        """

    return f"""
    <html>
    <head>
        <title>File Manager</title>
        <style>
            body {{ font-family: Arial; background:#f4f4f4; text-align:center; }}
            .box {{ background:white; padding:20px; margin:30px auto; width:400px; border-radius:10px; }}
            button {{ padding:8px; margin:5px; }}
            ul {{ list-style:none; padding:0; }}
        </style>
    </head>
    <body>

        <div class="box">
            <h2>📁 File Manager</h2>

            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button type="submit">⬆ Upload</button>
            </form>

            <hr>

            <h3>📂 Files</h3>
            <ul>
                {file_list_html if file_list_html else "<p>No files yet</p>"}
            </ul>

        </div>

    </body>
    </html>
    """

# ======================
# رفع ملف
# ======================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "uploaded", "filename": file.filename}

# ======================
# تحميل ملف
# ======================
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        return FileResponse(file_path)

    return {"error": "not found"}
