import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from werkzeug.datastructures import FileStorage
from services.pdf_service import validate_and_extract_pdf

from services.db_service import init_db, save_document, get_document_by_id

def test_backend_services():
    print("--- 1. Testing PDF Extraction ---")
    pdf_path = "scratch/sample_lecture.pdf"
    with open(pdf_path, 'rb') as f:
        file_storage = FileStorage(stream=f, filename="sample_lecture.pdf", content_type="application/pdf")
        text, filename, err = validate_and_extract_pdf(file_storage)
    
    assert err is None, f"PDF Extraction Error: {err}"
    assert "Supervised Learning" in text, "Extracted text missing expected keywords."
    print(f"Extraction successful! Extracted {len(text)} characters.")

    print("--- 2. Testing Database Services ---")
    init_db()
    
    dummy_notes = ["Machine learning is an AI subset.", "Overfitting captures noise."]
    dummy_quiz = [{"question": "What is overfitting?", "options": ["Noise capture", "Good generalisation", "Underfitting", "None"], "correct_answer": "Noise capture"}]
    dummy_mindmap = "# ML\n## Supervised"

    doc_id = save_document("sample_lecture.pdf", text, dummy_notes, dummy_quiz, dummy_mindmap)
    print(f"Saved document with ID: {doc_id}")

    fetched_doc = get_document_by_id(doc_id)
    assert fetched_doc is not None, "Failed to retrieve saved document."
    assert fetched_doc["filename"] == "sample_lecture.pdf", "Filename mismatch."
    assert len(fetched_doc["notes_json"]) == 2, "Notes JSON mismatch."
    print("Database insert & fetch successful!")

if __name__ == "__main__":
    test_backend_services()
