// Global Application State Variables
let currentDocId = null;
let currentStudyData = null;
let selectedFileObj = null;

// Initialize Event Listeners on DOM Load
document.addEventListener("DOMContentLoaded", () => {
    initDragAndDrop();
    initFileInput();
});

/* -------------------------------------------------------------
 * 1. DRAG AND DROP & FILE SELECTION LOGIC
 * ------------------------------------------------------------- */
function initDragAndDrop() {
    const dropZone = document.getElementById("dropZone");
    const uploadCard = document.getElementById("uploadSection");

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => uploadCard.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => uploadCard.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
}

function initFileInput() {
    const fileInput = document.getElementById("fileInput");
    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

function handleFileSelection(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError("Only PDF files (.pdf) are supported.");
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError("File size exceeds the 10MB limit.");
        return;
    }

    selectedFileObj = file;
    document.getElementById("selectedFileName").innerText = file.name;
    document.getElementById("fileSelectedInfo").style.display = "flex";
}

function clearSelectedFile() {
    selectedFileObj = null;
    document.getElementById("fileInput").value = "";
    document.getElementById("fileSelectedInfo").style.display = "none";
}

/* -------------------------------------------------------------
 * 2. UPLOADING & GEMINI AI PROCESSING (POST /api/upload)
 * ------------------------------------------------------------- */
function startUploadProcess() {
    if (!selectedFileObj) return;

    showLoadingState("Analyzing PDF with Gemini AI...");

    const formData = new FormData();
    formData.append("file", selectedFileObj);
    formData.append("subject", document.getElementById("subjectSelect").value);

    fetch("/api/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingState();
        if (data.error) {
            showError(data.error);
            return;
        }

        // Store active document session state
        currentDocId = data.doc_id;
        currentStudyData = data;

        // Render sections
        renderResultsDashboard(data);
    })
    .catch(err => {
        hideLoadingState();
        showError("Server error during PDF processing: " + err.message);
    });
}

function renderResultsDashboard(data) {
    // Hide upload & show results
    document.getElementById("uploadSection").style.display = "none";
    document.getElementById("resultsSection").style.display = "flex";
    document.getElementById("headerActions").style.display = "flex";

    // Set Document Name
    document.getElementById("activeDocName").innerText = data.filename || "Uploaded Lecture";

    // Show subject/course label, if the element exists in the markup
    const subjectLabelEl = document.getElementById("activeDocSubject");
    if (subjectLabelEl) {
        subjectLabelEl.innerText = data.subject || "General";
    }

    // Render Revision Notes
    renderNotes(data.notes);

    // Render Quiz Questions
    renderQuiz(data.quiz);
}

/* -------------------------------------------------------------
 * 3. REVISION NOTES RENDERING
 * ------------------------------------------------------------- */
function renderNotes(notesArray) {
    const notesList = document.getElementById("notesList");
    notesList.innerHTML = "";

    if (!notesArray || notesArray.length === 0) {
        notesList.innerHTML = "<li>No notes generated.</li>";
        return;
    }

    notesArray.forEach(note => {
        const li = document.createElement("li");
        li.innerText = note;
        notesList.appendChild(li);
    });
}

/* -------------------------------------------------------------
 * 4. INTERACTIVE QUIZ ENGINE
 * ------------------------------------------------------------- */
function renderQuiz(quizArray) {
    const container = document.getElementById("quizContainer");
    container.innerHTML = "";
    document.getElementById("quizScoreBadge").style.display = "none";

    if (!quizArray || quizArray.length === 0) {
        container.innerHTML = "<p>No quiz generated.</p>";
        return;
    }

    quizArray.forEach((q, qIndex) => {
        const quizItem = document.createElement("div");
        quizItem.className = "quiz-item";
        quizItem.setAttribute("data-qindex", qIndex);

        const qTitle = document.createElement("h4");
        qTitle.innerText = `${qIndex + 1}. ${q.question}`;
        quizItem.appendChild(qTitle);

        const optionsGroup = document.createElement("div");
        optionsGroup.className = "options-group";

        q.options.forEach((optText, optIndex) => {
            const label = document.createElement("label");
            label.className = "option-label";

            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = `question_${qIndex}`;
            radio.value = optText;

            const span = document.createElement("span");
            span.innerText = optText;

            label.appendChild(radio);
            label.appendChild(span);
            optionsGroup.appendChild(label);
        });

        quizItem.appendChild(optionsGroup);
        container.appendChild(quizItem);
    });
}

function submitQuiz() {
    if (!currentStudyData || !currentStudyData.quiz) return;

    const quizArray = currentStudyData.quiz;
    let score = 0;

    quizArray.forEach((q, qIndex) => {
        const quizItem = document.querySelector(`.quiz-item[data-qindex="${qIndex}"]`);
        const labels = quizItem.querySelectorAll(".option-label");
        const selectedRadio = quizItem.querySelector(`input[name="question_${qIndex}"]:checked`);

        labels.forEach(lbl => {
            lbl.classList.remove("correct-choice", "incorrect-choice");
            const radioVal = lbl.querySelector("input").value;

            // Highlight correct answer in green
            if (radioVal === q.correct_answer) {
                lbl.classList.add("correct-choice");
            }
        });

        if (selectedRadio) {
            if (selectedRadio.value === q.correct_answer) {
                score++;
            } else {
                // Highlight incorrect user pick in red
                selectedRadio.parentElement.classList.add("incorrect-choice");
            }
        }
    });

    // Display score badge
    document.getElementById("scoreVal").innerText = score;
    document.getElementById("quizScoreBadge").style.display = "inline-block";
}

function resetQuiz() {
    if (!currentStudyData || !currentStudyData.quiz) return;
    renderQuiz(currentStudyData.quiz);
}

/* -------------------------------------------------------------
 * 6. TAB SWITCHING SYSTEM
 * ------------------------------------------------------------- */
function switchTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(content => content.style.display = "none");

    if (tabName === 'notes') {
        document.getElementById("tabNotes").style.display = "block";
        event.currentTarget.classList.add("active");
    } else if (tabName === 'quiz') {
        document.getElementById("tabQuiz").style.display = "block";
        event.currentTarget.classList.add("active");
    }
}

/* -------------------------------------------------------------
 * 7. PDF Q&A ASSISTANT (POST /api/ask)
 * ------------------------------------------------------------- */
function sendStudentQuestion() {
    const inputEl = document.getElementById("qaInput");
    const questionText = inputEl.value.trim();

    if (!questionText) return;
    if (!currentDocId) {
        showError("Please upload a PDF document first.");
        return;
    }

    // Append Student Message Bubble
    appendChatMessage("user", questionText);
    inputEl.value = "";

    // Show bot typing placeholder
    const typingId = appendChatMessage("bot", "Thinking...");

    fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            doc_id: currentDocId,
            question: questionText
        })
    })
    .then(res => res.json())
    .then(data => {
        removeChatMessage(typingId);
        if (data.error) {
            appendChatMessage("bot", "Error: " + data.error);
        } else {
            appendChatMessage("bot", data.answer);
        }
    })
    .catch(err => {
        removeChatMessage(typingId);
        appendChatMessage("bot", "Error connecting to AI assistant: " + err.message);
    });
}

function handleQaKeyPress(event) {
    if (event.key === "Enter") {
        sendStudentQuestion();
    }
}

function appendChatMessage(sender, text) {
    const chatBox = document.getElementById("qaChatBox");
    const msgDiv = document.createElement("div");
    const msgId = "msg_" + Date.now();
    msgDiv.id = msgId;
    msgDiv.className = `chat-message ${sender}`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "avatar";
    avatarDiv.innerHTML = sender === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "bubble";
    bubbleDiv.innerText = text;

    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(bubbleDiv);
    chatBox.appendChild(msgDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
    return msgId;
}

function removeChatMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/* -------------------------------------------------------------
 * 8. EXPORT DOWNLOAD HANDLER (GET /api/export)
 * ------------------------------------------------------------- */
function toggleExportMenu() {
    const menu = document.getElementById("exportMenu");
    menu.classList.toggle("show");
}

function triggerExport(format) {
    toggleExportMenu();
    if (!currentDocId) return;

    window.location.href = `/api/export?doc_id=${currentDocId}&format=${format}`;
}

function resetUpload() {
    clearSelectedFile();
    currentDocId = null;
    currentStudyData = null;
    document.getElementById("resultsSection").style.display = "none";
    document.getElementById("headerActions").style.display = "none";
    document.getElementById("uploadSection").style.display = "block";
}

/* -------------------------------------------------------------
 * 9. UI HELPER FUNCTIONS
 * ------------------------------------------------------------- */
function showLoadingState(text) {
    document.getElementById("loadingStatusText").innerText = text;
    document.getElementById("uploadSection").style.display = "none";
    document.getElementById("loadingSection").style.display = "block";
}

function hideLoadingState() {
    document.getElementById("loadingSection").style.display = "none";
}

function showError(msg) {
    const toast = document.getElementById("errorToast");
    document.getElementById("errorMessageText").innerText = msg;
    toast.style.display = "flex";
    setTimeout(() => { hideError(); }, 6000);
}

function hideError() {
    document.getElementById("errorToast").style.display = "none";
}