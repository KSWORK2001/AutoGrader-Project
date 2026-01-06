# Examination AI

An intelligent exam grading system that automatically evaluates student answers by comparing them against multiple expert reference answers using AI-powered analysis.

## Overview

Examination AI is a desktop application that leverages large language models (LLMs) to provide fair, consistent, and detailed grading of student exam answers. The system compares student responses against three expert reference answers and provides:

- **Numerical score** (0-10 scale)
- **Detailed explanation** of the grading decision
- **Coverage analysis** showing what was covered vs. missing
- **Actionable suggestions** for improvement

## Features

- 🖼️ **Handwritten Answer Support**: Upload images of handwritten student answers with OCR extraction
- ⌨️ **Text Input Mode**: Direct text input for typed student answers
- 📚 **Multi-Expert Comparison**: Compare against up to 3 expert reference answers
- 🤖 **AI-Powered Grading**: Uses an OpenAI model for intelligent evaluation
- 📊 **Detailed Feedback**: Comprehensive scoring with explanations and improvement suggestions
- 📄 **Downloadable Reports**: One-click PDF report for graders/faculty
- 🖥️ **Desktop Application**: Clean, modern UI built with pywebview

## Technology Stack

- **Backend**: Python 3.x
  - `pywebview` - Desktop application framework
  - `openai` - LLM integration for grading
  - `base64` - Image encoding/decoding
- **Frontend**: HTML, CSS, JavaScript
  - Vanilla JavaScript (no frameworks)
  - Modern, responsive UI design
- **AI Model**: OpenAI (default: `gpt-5-nano`)

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.7+** installed
2. **An OpenAI API key** available as an environment variable
   - Set `OPENAI_API_KEY` before starting the app
3. **Qt backend** (optional but recommended for better UI rendering)

## Installation

1. **Clone or download the repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key** (Windows PowerShell):
   ```powershell
   $env:OPENAI_API_KEY="YOUR_API_KEY_HERE"
   ```

## Usage

### Running the Application

1. Navigate to the project directory:
   ```bash
   cd ExaminationAI
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. The desktop application window will open with the Examination AI interface.

### Grading Process

1. **Enter Question (Optional)**: Paste the exam question for context
2. **Choose Input Method**:
   - **Upload Image**: For handwritten answers (PNG, JPG, etc.)
   - **Enter Text**: For typed answers
3. **Upload Expert Answers**: Provide 1-3 text files containing expert reference answers
4. **Click "Grade Answer"**: The AI will analyze and provide detailed feedback
5. **Download Report** *(optional)*: After grading, click **Download PDF Report** to save a summary for graders/faculty

### Example Workflow

```
1. Upload student's handwritten answer image
2. Upload 3 expert answer text files (ExpertAnswer1.txt, ExpertAnswer2.txt, ExpertAnswer3.txt)
3. Click "Grade Answer"
4. Review the score, explanation, coverage analysis, and suggestions
```

## Project Structure

```
ExaminationAI/
├── app.py                  # Main application entry point
├── backend.py              # Backend logic and AI grading engine
├── index.html              # Frontend UI structure
├── script.js               # Frontend JavaScript logic
├── style.css               # UI styling
├── ExpertAnswer1.txt       # Sample expert answer 1
├── ExpertAnswer2.txt       # Sample expert answer 2
├── ExpertAnswers.txt       # Sample expert answer 3
├── StudentAnswers.txt      # Sample student answers
└── README.md               # This file
```

## How It Works

### Grading Algorithm

1. **Input Processing**: 
   - Extracts text from handwritten images using vision-capable LLM
   - Or accepts direct text input

2. **Expert Comparison**:
   - Analyzes all three expert answers to identify key points
   - Checks for coverage of important concepts, examples, formulas, and reasoning

3. **Evaluation Criteria**:
   - **10**: Fully correct, covers all important points, very clear
   - **8-9**: Mostly correct, minor omissions or clarity issues
   - **6-7**: Some important points covered but noticeable gaps
   - **3-5**: Major missing content or conceptual errors
   - **0-2**: Very little correct content, severely flawed

4. **Feedback Generation**:
   - Provides detailed explanation of score
   - Summarizes what was covered vs. missing
   - Offers specific suggestions for improvement

### AI Model Configuration

The system uses an OpenAI model by default. To change the model, modify the `model_name` parameter in `backend.py`:

```python
def __init__(self, model_name: str = "your-model-name"):
    self.model_name = model_name
```

## Sample Files

The project includes sample files for testing:
- `ExpertAnswer1.txt`, `ExpertAnswer2.txt`, `ExpertAnswers.txt` - Example expert answers
- `StudentAnswers.txt` - Example student answers
- `Gemini_Generated_Image_*.png` - Sample handwritten answer images

## Customization

### Modifying the Grading Prompt

Edit the `SYSTEM_PROMPT` in `backend.py` to adjust grading criteria, scoring scale, or output format.

### Changing the UI

Modify `style.css` for visual customization and `index.html` for layout changes.

## Troubleshooting

### Common Issues

1. **"pywebview API is not available"**
   - Ensure you're running the app via `python app.py`, not opening `index.html` directly

2. **"Missing OPENAI_API_KEY environment variable"**
   - Set `OPENAI_API_KEY` in your shell and restart the app
   - Confirm it’s available to Python in the same terminal session

3. **"Error calling OpenAI / model"**
   - Verify the key is valid and has access to the configured model
   - Check network connectivity/firewalls

4. **Image upload not working**
   - Ensure the image format is supported (PNG, JPG, JPEG)
   - Check file size isn't too large

4. **Qt backend issues**
   - Install Qt: `pip install PyQt5` or `pip install PyQt6`
   - Or remove the `gui="qt"` parameter in `app.py`

## Limitations

- Requires an OpenAI API key and network connectivity
- Grading quality depends on the AI model's capabilities
- Handwriting recognition accuracy varies with image quality
- Processing time depends on model size and hardware

## Future Enhancements

- [ ] Support for multiple AI models
- [ ] Batch grading of multiple students
- [ ] Export results to CSV/PDF
- [ ] Custom rubric configuration
- [ ] Historical grading analytics
- [ ] Multi-language support

## License

This project is provided as-is for educational and evaluation purposes.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests for improvements.

## Acknowledgments

- Built with the OpenAI API for LLM integration
- Uses [pywebview](https://pywebview.flowrl.com/) for desktop application framework
