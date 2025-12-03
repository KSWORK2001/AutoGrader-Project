const BASE_URL = "http://127.0.0.1:8000";

const fileInput = document.getElementById("fileInput");
const ocrBtn = document.getElementById("ocrBtn");
const gradeBtn = document.getElementById("gradeBtn");

const ocrOutput = document.getElementById("ocrOutput");
const resultBox = document.getElementById("resultBox");

ocrBtn.onclick = async () => {
    const files = fileInput.files;
    if (!files.length) return alert("Select exam images first!");

    let formData = new FormData();
    for (const f of files) formData.append("files", f);

    const res = await fetch(`${BASE_URL}/ocr/`, {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    ocrOutput.classList.remove("hidden");
    ocrOutput.innerHTML = "<h2>OCR Results</h2>" +
        data.pages.map(p =>
            `<h3>${p.filename}</h3><pre>${p.text}</pre>`
        ).join("<hr>");
};


gradeBtn.onclick = async () => {
    const questionText = document.getElementById("questionText").value;
    const studentAnswer = document.getElementById("studentAnswer").value;

    const expertAnswers = [...document.querySelectorAll(".expert")].map(e => e.value);

    const payload = {
        student_id: 1,
        answers: [
            {
                question_id: 1,
                question_text: questionText,
                student_answer: studentAnswer,
                expert_answers: expertAnswers,
                max_score: 10
            }
        ]
    };

    const res = await fetch(`${BASE_URL}/grade/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    const q = data.per_question[0];

    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `
        <h2>Grading Result</h2>
        <p><strong>Score:</strong> ${q.score}/10</p>
        <p><strong>Explanation:</strong> ${q.explanation}</p>
    `;
};
