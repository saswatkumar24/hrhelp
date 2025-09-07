# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

HRHelp is an intelligent HR assistant powered by Google Gemini AI and LangChain. It's a Flask web application that allows HR professionals to upload up to 25 resumes and analyze them using natural language queries.

**Technology Stack:**
- **Backend:** Python Flask 3.0.0
- **AI/ML:** Google Gemini Pro via LangChain, google-generativeai
- **Document Processing:** PyPDF2, python-docx for text extraction
- **Frontend:** HTML/CSS/JavaScript with Bootstrap
- **File Handling:** Support for PDF, DOCX, and ZIP files

## Essential Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Development Commands
```bash
# Run the application (development)
python app.py

# Run with custom host/port
python app.py  # Defaults to 0.0.0.0:8000

# Test Gemini models availability
python test_models.py

# Install production server
pip install gunicorn

# Run with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Testing and Debugging
```bash
# Enable debug mode (set in .env)
FLASK_DEBUG=True

# Check application health
curl http://localhost:8000/health

# Test file upload
curl -X POST http://localhost:8000/upload \
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"

# Test chat functionality
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who has the most experience?"}'
```

## Architecture Overview

### Core Components

**Main Application (`app.py`)**
- Flask application with session-based file management
- RESTful API endpoints for upload, chat, status, and session management
- Error handling and logging infrastructure
- File upload validation and temporary storage management

**Processing Pipeline:**
1. **File Validation** (`modules/validation.py`) - Validates file types, sizes, and content quality
2. **Resume Processing** (`modules/resume_processor.py`) - Extracts text from PDFs, DOCX, and ZIP files
3. **AI Analysis** (`modules/gemini_analyzer.py`) - Uses LangChain + Gemini for natural language processing

### Key Architectural Patterns

**Session-Based Processing:**
- Each upload session gets a unique UUID
- Files are stored in session-specific directories under `uploads/`
- Session data tracks loaded resumes and processing state
- Automatic cleanup on session clear

**Modular AI Analysis:**
- Different question types trigger different prompt templates
- Comparison questions vs. search questions vs. general questions
- Context creation from resume data with intelligent truncation
- Response parsing for structured data extraction

**Error Handling Strategy:**
- Comprehensive validation at multiple levels (file, content, API)
- Graceful degradation when individual files fail
- Detailed error messages for debugging and user feedback

## Configuration

### Required Environment Variables
```bash
GOOGLE_API_KEY=your_google_gemini_api_key_here  # Required
FLASK_SECRET_KEY=your_secret_key_here          # Auto-generated if not set
FLASK_DEBUG=True                               # Development only
```

### Optional Configuration
```bash
MAX_CONTENT_LENGTH=16777216  # 16MB max file size
UPLOAD_FOLDER=uploads        # Upload directory
MAX_FILES=25                 # Maximum files per session
```

### File Processing Limits
- **Supported formats:** PDF, DOCX, ZIP (containing PDF/DOCX)
- **Maximum files:** 25 per session
- **File size limit:** 16MB per file
- **Content validation:** Minimum 100 characters, resume-specific keywords required

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main web interface |
| `/upload` | POST | Process and validate resume uploads |
| `/chat` | POST | Send natural language questions about resumes |
| `/status` | GET | Check current session state and resume summary |
| `/clear` | GET | Clear session and cleanup uploaded files |
| `/health` | GET | Application health check and Gemini API status |

## Common Development Tasks

### Adding New File Types
1. Update `ALLOWED_EXTENSIONS` in `config.py`
2. Add text extraction method in `resume_processor.py`
3. Update validation logic in `validation.py`

### Modifying AI Analysis
- **Prompt templates:** Edit templates in `gemini_analyzer.py`
- **Question categorization:** Modify `_is_comparison_question()` and `_is_search_question()`
- **Response parsing:** Update `_extract_table_from_response()` method

### Customizing Validation Rules
- **File validation:** Modify `FileValidator` class in `validation.py`
- **Resume content validation:** Update `ResumeValidator` with new patterns or requirements
- **Quality metrics:** Adjust scoring in `validate_resume_quality()`

## Development Notes

### Session Management
- Sessions are automatically created on file upload
- Session data is stored in Flask sessions (server-side)
- File cleanup happens on session clear or server restart
- Session IDs are UUIDs for security

### Gemini Integration
- Uses `gemini-1.5-flash` model with temperature 0.1 for consistency
- LangChain integration for structured prompting
- Context truncation at 2000 characters per resume for API limits
- Error handling for API rate limits and failures

### File Processing Workflow
1. **Upload Validation:** File type, size, count validation
2. **Text Extraction:** Format-specific text extraction with error handling
3. **Content Validation:** Resume-specific content verification
4. **AI Loading:** Context preparation and analyzer initialization
5. **Query Processing:** Natural language analysis with structured responses

### Error Recovery
- Individual file failures don't stop batch processing
- Partial uploads are supported with warnings
- API errors are caught and reported with helpful messages
- Session state is preserved across most error conditions

## Security Considerations

- File type validation prevents malicious uploads
- Secure filename handling prevents directory traversal
- Session-based isolation prevents cross-user data access
- Input sanitization on all user-provided content
- API key protection through environment variables
