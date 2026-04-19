import os
import base64
from pypdf import PdfReader
from openai import OpenAI


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"[PDF ERROR] {e}")
    return text.strip()


def ocr_pdf_with_openai(file_path: str) -> str:
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(file_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Extract all readable text from this document."},
                        {
                            "type": "input_file",
                            "filename": os.path.basename(file_path),
                            "file_data": file_data,
                            "detail": "high",
                        },
                    ],
                }
            ],
        )

        return response.output_text or ""
    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return ""


def extract_text(file_path: str) -> str:
    print(f"[PROCESSING] {file_path}")
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        print("[INFO] No text found, using OpenAI OCR...")
        text = ocr_pdf_with_openai(file_path)
    return text.strip()