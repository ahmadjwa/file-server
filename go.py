from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import os
import shutil

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# الصفحة الرئيسية (واجهة احترافية)
# =========================
@app.get("/", response_class=HTMLResponse)
def home():
    files = os.listdir(UPLOAD_DIR)

    cards = ""
    for f in files:
        cards += f"""
        <div class="card">
            <div class="name">{f}</div>
            <div class="actions">
                <a href="/download/{f}"><button>⬇ Download</button></a>
                <a href="/delete/{f}"><button class="delete">🗑 Delete</button></a>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Cloud File Manager</title>
        <style>
            body {{
                font-family: Arial;
                background: #f1f5f9;
                text-align: center;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 80%;
                margin: auto;
                padding: 20px;
            }}
            h1 {{
                color: #333;
            }}
            .upload-box {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            input {{
                padding: 10px;
            }}
            button {{
                padding: 10px 15px;
                margin: 5px;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }}
            .card {{
                background: white;
                padding: 15px;
                margin: 10px;
                border-radius: 10px;
                display: inline-block;
                width: 250px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .name {{
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .delete {{
                background: red;
                color: white;
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <h1>☁ Cloud File Manager</h1>

            <div class="upload-box">
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <button type="submit">⬆ Upload</button>
                </form>
            </div>

            <h2>📁 Your Files</h2>
            <div>
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
