import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    print("--- 1. Testing GET / (Landing Page) ---")
    res = requests.get(f"{BASE_URL}/")
    assert res.status_code == 200, f"Landing page failed with status {res.status_code}"
    assert "Student Workspace" in res.text, "Landing page title missing."
    print("GET / OK!")

    print("--- 2. Testing POST /api/upload (PDF Upload) ---")
    pdf_path = "scratch/sample_lecture.pdf"
    with open(pdf_path, 'rb') as f:
        files = {'file': ('sample_lecture.pdf', f, 'application/pdf')}
        res = requests.post(f"{BASE_URL}/api/upload", files=files)

    print(f"Upload response status: {res.status_code}")
    print(f"Upload response JSON: {res.json()}")

    if res.status_code == 200:
        doc_id = res.json().get("doc_id")
        print(f"Uploaded successfully! Document ID = {doc_id}")

        print("--- 3. Testing POST /api/ask (Q&A Endpoint) ---")
        ask_res = requests.post(
            f"{BASE_URL}/api/ask",
            json={"doc_id": doc_id, "question": "What is machine learning?"}
        )
        print(f"Ask response status: {ask_res.status_code}")
        print(f"Ask response JSON: {ask_res.json()}")

        print("--- 4. Testing GET /api/export (TXT Export) ---")
        export_txt = requests.get(f"{BASE_URL}/api/export?doc_id={doc_id}&format=txt")
        assert export_txt.status_code == 200, "TXT export failed."
        print(f"Exported TXT size: {len(export_txt.content)} bytes.")

        print("--- 5. Testing GET /api/export (PDF Export) ---")
        export_pdf = requests.get(f"{BASE_URL}/api/export?doc_id={doc_id}&format=pdf")
        assert export_pdf.status_code == 200, "PDF export failed."
        print(f"Exported PDF size: {len(export_pdf.content)} bytes.")
    else:
        print("Upload returned error (expected if GEMINI_API_KEY is not set yet):", res.json())

if __name__ == "__main__":
    test_api()
