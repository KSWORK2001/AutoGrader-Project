// script.js
const form = document.getElementById("grade-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const gradeBtn = document.getElementById("grade-btn");
const downloadPdfBtn = document.getElementById("download-pdf-btn");
const answerModeRadios = document.querySelectorAll("input[name='answerMode']");
const answerImageBlock = document.getElementById("answer-image-block");
const answerTextBlock = document.getElementById("answer-text-block");
let lastReportData = null;

function syncAnswerModeActiveUI() {
    const selected = document.querySelector("input[name='answerMode']:checked");
    const options = document.querySelectorAll(".toggle-option");
    options.forEach((opt) => opt.classList.remove("active"));

    if (!selected) return;
    const label = selected.closest(".toggle-option");
    if (label) label.classList.add("active");
}

answerModeRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
        if (radio.value === "image") {
            answerImageBlock.classList.remove("hidden");
            answerTextBlock.classList.add("hidden");
        } else {
            answerImageBlock.classList.add("hidden");
            answerTextBlock.classList.remove("hidden");
        }

        syncAnswerModeActiveUI();
    });
});

syncAnswerModeActiveUI();

async function fileToBase64(file) {
    if (!file) return "";
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result; // e.g. "data:image/png;base64,AAAA..."
            const base64 = typeof result === "string" ? result.split(",")[1] : "";
            resolve(base64 || "");
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

async function fileToText(file) {
    if (!file) return "";
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            resolve(reader.result || "");
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsText(file);
    });
}

function setLoading(isLoading, message = "") {
    if (isLoading) {
        gradeBtn.disabled = true;
        statusEl.textContent = message || "Grading in progress...";
        statusEl.classList.add("loading");
    } else {
        gradeBtn.disabled = false;
        statusEl.textContent = message || "";
        statusEl.classList.remove("loading");
    }
}

function renderResult(data) {
    if (!data) {
        resultEl.innerHTML = `<p class="error">No response from backend.</p>`;
        resetReportData();
        return;
    }

    if (data.error) {
        resultEl.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        resetReportData();
        return;
    }

    const score = data.score;
    const explanation = data.explanation || "";
    const coverage = data.coverage_summary || "";
    const suggestions = data.suggestions || "";
    const raw = data.raw_model_response || "";

    let scoreClass = "";
    if (typeof score === "number") {
        if (score >= 8) scoreClass = "high";
        else if (score >= 5) scoreClass = "medium";
        else scoreClass = "low";
    }

    const scoreLabel =
        typeof score === "number" ? `${score} / 10` : "N/A (parse error)";

    resultEl.innerHTML = `
    <div class="result-card">
      <div class="score-badge ${scoreClass}">
        <span>Score:</span>
        <span>${scoreLabel}</span>
      </div>

      <div>
        <p class="section-title">Explanation</p>
        <p class="section-body">${escapeHtml(explanation)}</p>
      </div>

      <div>
        <p class="section-title">Coverage vs Expert Answers</p>
        <p class="section-body">${escapeHtml(coverage)}</p>
      </div>

      <div>
        <p class="section-title">Suggestions for Improvement</p>
        <p class="section-body">${escapeHtml(suggestions)}</p>
      </div>

      <details style="margin-top:0.6rem;">
        <summary>Raw model response</summary>
        <div class="raw-response">${escapeHtml(raw)}</div>
      </details>
    </div>
  `;
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const answerMode = document.querySelector("input[name='answerMode']:checked").value;

    const expert1File = document.getElementById("expert1").files[0];
    const expert2File = document.getElementById("expert2").files[0];
    const expert3File = document.getElementById("expert3").files[0];
    const questionText = document.getElementById("question").value.trim();

    let studentImageBase64 = "";
    let studentText = "";

    // -----------------------------
    // IMAGE MODE
    // -----------------------------
    if (answerMode === "image") {
        const imageFile = document.getElementById("student-image").files[0];

        if (!imageFile) {
            alert("Please upload the student's handwritten answer image.");
            return;
        }

        studentImageBase64 = await fileToBase64(imageFile);
    }

    // -----------------------------
    // TEXT MODE
    // -----------------------------
    else {
        studentText = document.getElementById("student-text").value.trim();

        if (!studentText) {
            alert("Please enter the student's answer text.");
            return;
        }
    }

    if (!window.pywebview || !window.pywebview.api) {
        alert("pywebview API is not available. Are you running the desktop app?");
        return;
    }

    setLoading(true, "Grading in progress...");
    resetReportData();

    try {
        const [expert1Text, expert2Text, expert3Text] = await Promise.all([
            fileToText(expert1File),
            fileToText(expert2File),
            fileToText(expert3File),
        ]);

        const payload = {
            question: questionText,
            studentImageBase64,
            studentText,
            expert1: expert1Text,
            expert2: expert2Text,
            expert3: expert3Text,
        };

        const result = await window.pywebview.api.grade_answer(payload);
        renderResult(result);
        if (result && !result.error) {
            setReportData({
                question: questionText,
                mode: answerMode === "image" ? "Handwritten image upload" : "Typed text entry",
                score: typeof result.score === "number" ? result.score : null,
                explanation: result.explanation || "",
                coverage: result.coverage_summary || "",
                suggestions: result.suggestions || "",
                raw: result.raw_model_response || "",
            });
        }
        setLoading(false, "Done!");
    } catch (err) {
        console.error(err);
        setLoading(false, "Error occurred.");
        resultEl.innerHTML = `<p class="error">Error: ${String(err)}</p>`;
        resetReportData();
    }
});

function togglePdfButton(enabled) {
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = !enabled;
    }
}

function resetReportData() {
    lastReportData = null;
    togglePdfButton(false);
}

function setReportData(data) {
    lastReportData = {
        ...data,
        generatedAt: new Date().toLocaleString(),
    };
    togglePdfButton(true);
}

if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener("click", () => {
        if (!lastReportData) {
            alert("Run a grading first to generate the PDF report.");
            return;
        }

        try {
            const pdfBlob = createSimplePdf(lastReportData);
            const link = document.createElement("a");
            const url = URL.createObjectURL(pdfBlob);
            link.href = url;
            link.download = `examination-report-${Date.now()}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            setTimeout(() => URL.revokeObjectURL(url), 2000);
        } catch (err) {
            console.error(err);
            alert(`Failed to generate PDF: ${err.message || err}`);
        }
    });
}

function createSimplePdf(report) {
    const lines = buildReportLines(report);
    const pageHeight = 792; // 11in * 72dpi
    const pageWidth = 612; // 8.5in * 72dpi
    const margin = 40;
    const lineHeight = 16;
    const maxLinesPerPage = Math.max(1, Math.floor((pageHeight - margin * 2) / lineHeight));
    const chunks = [];

    for (let i = 0; i < lines.length; i += maxLinesPerPage) {
        chunks.push(lines.slice(i, i + maxLinesPerPage));
    }

    if (chunks.length === 0) {
        chunks.push(["No report content available."]);
    }

    const encoder = new TextEncoder();
    const objects = [];

    const setObject = (index, content) => {
        objects[index] = content;
    };

    const addObject = (content) => {
        objects.push(content);
        return objects.length;
    };

    // Placeholders for catalog (1) and pages (2)
    setObject(0, "");
    setObject(1, "");

    const fontObjNum = addObject("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
    const pageObjNums = [];

    chunks.forEach((chunkLines) => {
        const textOps = chunkLines.map((line, index) => {
            const y = pageHeight - margin - index * lineHeight;
            return `BT /F1 11 Tf 1 0 0 1 ${margin} ${y.toFixed(2)} Tm (${escapePdfText(line)}) Tj ET`;
        });

        const contentStream = textOps.join("\n");
        const streamLength = encoder.encode(contentStream).length;
        const contentObjNum = addObject(`<< /Length ${streamLength} >>\nstream\n${contentStream}\nendstream`);

        const pageObjNum = addObject(
            [
                "<< /Type /Page",
                " /Parent 2 0 R",
                ` /MediaBox [0 0 ${pageWidth} ${pageHeight}]`,
                ` /Contents ${contentObjNum} 0 R`,
                ` /Resources << /Font << /F1 ${fontObjNum} 0 R >> >>`,
                ">>",
            ].join("")
        );

        pageObjNums.push(pageObjNum);
    });

    if (pageObjNums.length === 0) {
        throw new Error("Unable to build PDF pages.");
    }

    setObject(
        1,
        `<< /Type /Pages /Kids [${pageObjNums.map((num) => `${num} 0 R`).join(" ")}] /Count ${pageObjNums.length} >>`
    );
    setObject(0, "<< /Type /Catalog /Pages 2 0 R >>");

    let pdf = "%PDF-1.4\n";
    const offsets = [];

    objects.forEach((obj, idx) => {
        if (!obj) {
            throw new Error(`Missing PDF object at index ${idx}`);
        }
        offsets[idx] = pdf.length;
        pdf += `${idx + 1} 0 obj\n${obj}\nendobj\n`;
    });

    const xrefPosition = pdf.length;
    pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
    offsets.forEach((offset) => {
        pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
    });
    pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefPosition}\n%%EOF`;

    return new Blob([pdf], { type: "application/pdf" });
}

function buildReportLines(report) {
    const lines = [];
    const wrap = (text, max = 80) => wrapText(text, max);

    lines.push("Examination AI Grading Report");
    lines.push("----------------------------------------");
    lines.push(`Generated: ${report.generatedAt || "N/A"}`);
    lines.push(`Input Mode: ${report.mode || "Unknown"}`);
    lines.push("");

    lines.push("Question:");
    lines.push(...wrap(report.question || "No question context provided."));
    lines.push("");

    const scoreLabel =
        typeof report.score === "number" ? `${report.score} / 10` : "Not available (model parsing issue)";
    lines.push(`Score: ${scoreLabel}`);
    lines.push("");

    lines.push("Explanation:");
    lines.push(...wrap(report.explanation || "—"));
    lines.push("");

    lines.push("Coverage vs Expert Answers:");
    lines.push(...wrap(report.coverage || "—"));
    lines.push("");

    lines.push("Suggestions:");
    lines.push(...wrap(report.suggestions || "—"));
    lines.push("");

    const rawPreview = report.raw
        ? `${report.raw.slice(0, 1200)}${report.raw.length > 1200 ? " [...]" : ""}`
        : "—";
    lines.push("Raw Model Response (truncated):");
    lines.push(...wrap(rawPreview));

    return lines;
}

function wrapText(text, maxLength) {
    if (!text) return [""];
    const normalized = String(text).replace(/\r\n/g, "\n").split("\n");
    const result = [];

    normalized.forEach((paragraph) => {
        const trimmed = paragraph.trim();
        if (!trimmed) {
            result.push("");
            return;
        }

        let currentLine = "";
        trimmed.split(/\s+/).forEach((word) => {
            const candidate = currentLine ? `${currentLine} ${word}` : word;
            if (candidate.length > maxLength && currentLine) {
                result.push(currentLine);
                currentLine = word;
            } else {
                currentLine = candidate;
            }
        });

        if (currentLine) {
            result.push(currentLine);
        }
    });

    return result.length ? result : [""];
}

function escapePdfText(text) {
    return String(text)
        .replace(/\\/g, "\\\\")
        .replace(/\(/g, "\\(")
        .replace(/\)/g, "\\)");
}
