import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

# Maximum allowed file size in bytes (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf'}

def is_allowed_file(filename):
    """
    Checks if the uploaded file has a .pdf extension.
    Returns True if valid, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_and_extract_pdf(file_storage, upload_folder="uploads"):
    """
    Validates the uploaded PDF file (extension, size) and extracts text content.
    First tries pdfplumber (native extraction), then falls back to OCR if empty.
    
    Why both methods exist:
    - Native extraction (pdfplumber) is fast, accurate, and works for standard PDFs (e.g., exported from Word/PPT).
    - OCR extraction (tesseract) is slower but necessary for scanned documents or image-only PDFs that have no embedded text layer.
    
    :param file_storage: Werkzeug FileStorage object
    :param upload_folder: Directory to temporarily store uploaded files
    :return: (extracted_text, filename, error_message, num_pages)
    """
    filename = file_storage.filename
    if not filename or not is_allowed_file(filename):
        return None, None, "Invalid file format. Only PDF files (.pdf) are supported.", 0

    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    
    # Save file temporarily to disk to read size and content safely
    file_storage.save(file_path)

    # Check file size (max 10MB)
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        os.remove(file_path)
        return None, None, "File size exceeds the 10MB limit.", 0

    extracted_text = ""
    num_pages = 0
    
    try:
        # Step 1: Try Native PDF Extraction with pdfplumber
        print("[PDF Extraction] Attempting native extraction with pdfplumber...")
        extracted_text_list = []
        with pdfplumber.open(file_path) as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages:
                # Concatenate with "" fallback so one failed page doesn't crash the loop
                text = page.extract_text() or ""
                extracted_text_list.append(text)
                
        extracted_text = "\n\n".join(extracted_text_list).strip()

        # Step 2: Fallback to OCR if native extraction yields empty text
        if not extracted_text:
            print("[PDF Extraction] Native extraction empty. Falling back to OCR...")
            
            # Note: poppler must be installed on the system for pdf2image to work
            images = convert_from_path(file_path)
            num_pages = len(images)
            ocr_text_list = []
            
            for i, img in enumerate(images):
                print(f"[PDF Extraction] Running OCR on page {i + 1}/{num_pages}...")
                text = pytesseract.image_to_string(img) or ""
                ocr_text_list.append(text)
                
            extracted_text = "\n\n".join(ocr_text_list).strip()
            
            if extracted_text:
                print("[PDF Extraction] OCR extraction successful.")
        else:
            print("[PDF Extraction] Native extraction successful.")

        if not extracted_text:
            return None, None, "Could not extract any readable text from the PDF using native extraction or OCR. It may be corrupt or purely low-quality images.", num_pages

        return extracted_text, filename, None, num_pages

    except Exception as e:
        return None, None, f"Failed to extract text from PDF: {str(e)}", num_pages
    finally:
        # Clean up temporary file after extraction
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
