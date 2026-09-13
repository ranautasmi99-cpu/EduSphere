# 🎓 EduSphere — AI-Powered Student Workspace

> **Everything you need to study, in one place.**

EduSphere is an AI-powered student workspace that turns a lecture PDF into a complete revision package.

Instead of manually reading a lecture, creating notes, preparing practice questions, and searching for explanations, students can upload their lecture material once and let EduSphere handle the repetitive preparation work.

---

## 💡 The Problem

Students often spend a significant amount of time preparing study material from lecture content.

A typical workflow looks like:

**Lecture PDF → Read → Make Notes → Create Questions → Revise → Search for Doubts**

This involves repetitive work and often requires switching between multiple tools.

### Our Solution

EduSphere focuses on one simple workflow:

**Upload Lecture PDF → AI Generates Study Material → Revise & Practice**

The uploaded lecture remains at the center of the entire workflow.

---

## ✨ Key Features

### 📄 AI Revision Notes

Upload a lecture PDF and EduSphere generates structured revision notes from the document.

### 📝 AI-Generated Practice Quiz

A **5-question practice quiz** is generated from the same lecture content, allowing students to test their understanding immediately.

### 💬 Contextual Q&A

Students can ask questions about the uploaded lecture and receive AI-generated answers based on the document content.

### 📤 Export Study Material

Notes and quiz content can be exported in shareable formats:

* `.txt`
* `.pdf`

### 🎯 Light Personalization

Students can select their subject/course before processing the document.

Supported options include:

* Computer Science
* Mathematics
* Physics
* Chemistry
* Biology
* General
* Other

The selected subject is used as additional context when generating the study material.

---

## 🤖 How It Works

```text
                Student
                   │
                   ▼
             Upload Lecture PDF
                   │
                   ▼
             Flask Backend
                   │
                   ▼
          Extract PDF Text
             (pdfplumber)
                   │
                   ▼
            Gemini AI Model
                   │
          ┌────────┴────────┐
          ▼                 ▼
    Revision Notes      5-Question Quiz
          │                 │
          └────────┬────────┘
                   ▼
             EduSphere UI
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
        Revise    Quiz      Ask
                            Questions
                   │
                   ▼
                 Export
```

---

## 🧠 AI Workflow

When a student uploads a PDF:

1. The Flask backend receives the file.
2. The PDF is validated and its text is extracted using **pdfplumber**.
3. The extracted content is sent to the **Google Gemini API**.
4. Gemini generates structured revision notes and five practice questions.
5. The backend parses the generated response.
6. The study material is sent to the frontend.
7. The student can revise, take the quiz, ask questions, or export the material.

For contextual Q&A, the student's question is processed together with the uploaded lecture content so that the response remains related to the selected material.

---

## 🛠️ Technology Stack

| Layer          | Technology            |
| -------------- | --------------------- |
| Frontend       | HTML, CSS, JavaScript |
| Backend        | Python, Flask         |
| AI             | Google Gemini API     |
| PDF Processing | pdfplumber            |
| Database       | SQLite / MySQL        |
| Templating     | Jinja2                |
| Export         | ReportLab             |
| Configuration  | python-dotenv         |

---

## 📁 Project Structure

```text
EduSphere/
│
├── app.py
│
├── services/
│   ├── ai_service.py
│   ├── db_service.py
│   └── pdf_service.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── templates/
│   └── index.html
│
├── data/
│   └── student_workspace.db
│
├── .env
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd EduSphere
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=edusphere
```

> **Important:** Never commit your `.env` file or expose your API key publicly.

### 5. Run the application

```bash
python app.py
```

Open the local URL shown by Flask in your browser.

---

## 🔑 API Key

EduSphere uses the **Google Gemini API** for AI-powered document understanding and content generation.

The API key should be stored in `.env` and loaded using environment variables.

Example:

```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
```

---

## 📌 Core Problem Statement Alignment

EduSphere follows the hackathon's **AI-Powered Student Workspace** requirement by focusing on one primary flow:

> **Lecture PDF → Revision Notes + 5-Question Practice Quiz**

### Must-Have

* ✅ Single end-to-end AI workflow
* ✅ Lecture PDF processing
* ✅ AI-generated revision notes
* ✅ AI-generated 5-question quiz
* ✅ Study material generated from the same uploaded content

### Bonus Features

* ❌ Multiple file formats — currently PDF-focused
* ✅ Export notes/quiz in shareable formats
* ✅ Subject/course personalization

The project intentionally focuses on completing the core workflow rather than adding unrelated features.

---

## 🎯 Why EduSphere?

The goal isn't to build another general-purpose chatbot.

The AI model is only one part of the solution. The main focus is creating a **focused student workflow** around it.

Instead of:

```text
PDF
 ↓
ChatGPT
 ↓
Copy Notes
 ↓
Another Tool
 ↓
Create Quiz
 ↓
Search for Doubts
```

EduSphere provides:

```text
              One Lecture PDF
                    ↓
              ┌─────────────┐
              │  EduSphere  │
              └─────────────┘
                 ↓    ↓    ↓
              Notes  Quiz  Q&A
                 \    |    /
                  \   |   /
                   Export
```

This reduces the repetitive preparation work students normally perform before studying.

---

## ⚠️ Current Limitations

* Currently optimized for **text-based PDFs**.
* Scanned/image-only PDFs may require OCR support.
* AI-generated content can occasionally contain inaccuracies and should be verified by students.
* The application depends on availability of the Gemini API.

---

## 🔮 Future Improvements

Possible future enhancements include:

* Support for DOCX and PPTX files
* OCR for scanned lecture materials
* More advanced personalization based on learning preferences
* Improved citation and source highlighting
* Study progress tracking
* More customizable quiz difficulty
* Authentication and student profiles

---



## 📜 License

This project was developed as a student hackathon project.

---

### Made with Python, Flask & Gemini AI

**EduSphere — Everything you need to study, in one place.**
