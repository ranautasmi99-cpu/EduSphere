import os
import io
import json
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv

from services.pdf_service import validate_and_extract_pdf
from services.ai_service import generate_study_materials, answer_student_question
from services.db_service import init_db, save_document, get_document_by_id

# Load environment variables from .env file
load_dotenv()

# Initialize Flask Application
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max payload limit

# Initialize database table on server startup
init_db()

@app.route('/')
def index():
    """
    Renders the main single-page student study workspace web interface.
    """
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """
    Endpoint 1: POST /api/upload
    -----------------------------
    Accepts a PDF file upload, extracts text, calls Gemini for structured
    notes + quiz + mindmap, stores result in MySQL, and returns JSON.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded in request."}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    # Personalization: which subject/course this material belongs to.
    # Defaults to "General" if the frontend doesn't send one.
    subject = request.form.get('subject', 'General').strip() or 'General'

    # Step 1: Validate and extract text from PDF file
    extracted_text, filename, error_msg, num_pages = validate_and_extract_pdf(uploaded_file)
    
    # DEBUG LOGGING (As requested by user)
    print("=" * 50)
    print(f"DEBUG: PDF Extraction Stats for '{filename}'")
    print(f"- Pages detected: {num_pages}")
    print(f"- Extracted text length (before empty check): {len(extracted_text) if extracted_text else 0} chars")
    if extracted_text:
        print(f"- First 200 chars:\n{extracted_text[:200]}")
    else:
        print("- First 200 chars: [None/Empty]")
    print("=" * 50)

    if error_msg:
        return jsonify({"error": error_msg}), 400

    # Step 2: Call Gemini API to generate structured revision notes, quiz, and mindmap
    try:
        study_data = generate_study_materials(extracted_text, subject=subject)
    except ValueError as val_err:
        return jsonify({"error": f"AI Parsing Error: {str(val_err)}"}), 500
    except Exception as ai_err:
        return jsonify({"error": f"AI Processing Error: {str(ai_err)}"}), 500

    # Step 3: Save extracted text and generated JSON into MySQL database
    notes_json = study_data.get("notes", [])
    quiz_json = study_data.get("quiz", [])
    mindmap_markdown = study_data.get("mindmap_markdown", "")

    doc_id = save_document(
        filename=filename,
        extracted_text=extracted_text,
        notes_json=notes_json,
        quiz_json=quiz_json,
        mindmap_markdown=mindmap_markdown,
        subject=subject
    )

    # Step 4: Return result to frontend
    return jsonify({
        "success": True,
        "doc_id": doc_id,
        "filename": filename,
        "subject": subject,
        "notes": notes_json,
        "quiz": quiz_json
    }), 200

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Endpoint 2: POST /api/ask
    --------------------------
    Accepts student question and doc_id, retrieves extracted text from MySQL,
    calls Gemini API, and returns concise plain-text answer.
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    doc_id = data.get("doc_id")

    if not question:
        return jsonify({"error": "Question field cannot be empty."}), 400

    # Fetch document text from MySQL database
    doc_record = get_document_by_id(doc_id)
    if not doc_record or not doc_record.get("extracted_text"):
        return jsonify({"error": "No active document found. Please upload a PDF first."}), 404

    extracted_text = doc_record["extracted_text"]

    try:
        answer = answer_student_question(extracted_text, question)
        return jsonify({
            "success": True,
            "question": question,
            "answer": answer
        }), 200
    except Exception as err:
        return jsonify({"error": f"Failed to answer question: {str(err)}"}), 500

@app.route('/api/export', methods=['GET'])
def export_materials():
    """
    Endpoint 3: GET /api/export
    ----------------------------
    Exports generated revision notes and quiz as downloadable TXT or PDF file.
    URL Query Params: doc_id (optional), format ('txt' or 'pdf')
    """
    doc_id = request.args.get('doc_id', type=int)
    export_format = request.args.get('format', 'txt').lower()

    doc_record = get_document_by_id(doc_id)
    if not doc_record:
        return jsonify({"error": "Document not found to export."}), 404

    filename = doc_record.get("filename", "Lecture_Notes").rsplit('.', 1)[0]
    notes = doc_record.get("notes_json") or []
    quiz = doc_record.get("quiz_json") or []

    # Export as Plain Text TXT
    if export_format == 'txt':
        content = []
        content.append(f"==================================================")
        content.append(f" REVISION NOTES & QUIZ: {filename}")
        content.append(f"==================================================\n")
        
        content.append("--- REVISION NOTES ---")
        for i, note in enumerate(notes, 1):
            content.append(f"{i}. {note}")
        content.append("\n")

        content.append("--- 5-QUESTION PRACTICE QUIZ ---")
        for i, q in enumerate(quiz, 1):
            content.append(f"Q{i}: {q.get('question')}")
            for opt in q.get('options', []):
                content.append(f"   [ ] {opt}")
            content.append(f"Answer: {q.get('correct_answer')}\n")

        buffer = io.BytesIO("\n".join(content).encode('utf-8'))
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{filename}_study_materials.txt",
            mimetype="text/plain"
        )

    # Export as PDF using reportlab
    elif export_format == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1E293B'), spaceAfter=12)
            heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#2563EB'), spaceBefore=12, spaceAfter=8)
            body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#334155'), leading=14, spaceAfter=6)
            bold_body = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')

            story = []
            story.append(Paragraph(f"Study Workspace: {filename}", title_style))
            story.append(Spacer(1, 10))

            # Notes Section
            story.append(Paragraph("Revision Notes", heading_style))
            for note in notes:
                story.append(Paragraph(f"• {note}", body_style))
            story.append(Spacer(1, 15))

            # Quiz Section
            story.append(Paragraph("Practice Quiz", heading_style))
            for i, q in enumerate(quiz, 1):
                story.append(Paragraph(f"<b>Q{i}: {q.get('question')}</b>", body_style))
                for opt in q.get('options', []):
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;[ ] {opt}", body_style))
                story.append(Paragraph(f"<b>Correct Answer:</b> {q.get('correct_answer')}", bold_body))
                story.append(Spacer(1, 8))

            doc.build(story)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{filename}_study_materials.pdf",
                mimetype="application/pdf"
            )

        except Exception as pdf_err:
            return jsonify({"error": f"PDF Export Error: {str(pdf_err)}"}), 500

    else:
        return jsonify({"error": "Unsupported export format. Use 'txt' or 'pdf'."}), 400

if __name__ == '__main__':
    # Run development server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)