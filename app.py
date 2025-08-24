from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF for PDF
from docx import Document  # python-docx for Word
import os
import uuid
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nuvia-ai.vercel.app/",
        "http://localhost:5173",
        "http://127.0.0.1:8000"],  # Change "*" to specific domains for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to extract text from PDF
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

import google.generativeai as genai
import os
from PIL import Image

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

def extract_text_gemini(image_path: str) -> str:
    img = Image.open(image_path)
    response = model.generate_content(
        ["Extract all readable text from this image and only return the text with no \"\\n\" or any similar thing:", img]
    )
    return response.text



@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    try:
        file_ext = os.path.splitext(file.filename)[1].lower()
        temp_file = f"temp_{uuid.uuid4().hex}{file_ext}"

        # Always reset file pointer and write binary
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        if file_ext == ".pdf":
            extracted_text = extract_text_from_pdf(temp_file)
        elif file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            extracted_text = extract_text_gemini(temp_file)
        elif file_ext == ".txt":
            with open(temp_file, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
        else:
            os.remove(temp_file)
            raise HTTPException(status_code=400, detail="Unsupported file format")

        os.remove(temp_file)

        return {"extracted_text": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)