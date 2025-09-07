# HR Resume Analyzer

🤖 **An intelligent HR assistant powered by Google Gemini AI and LangChain**

A web application that allows HR professionals to upload up to 25 resumes and analyze them using natural language queries. Get instant insights about candidates' experience, skills, and qualifications with AI-powered analysis.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![LangChain](https://img.shields.io/badge/langchain-0.1.0-orange.svg)
![Google Gemini](https://img.shields.io/badge/google--gemini-pro-red.svg)

## ✨ Features

- **Multi-format Support**: Upload PDF, DOCX, and ZIP files containing resumes
- **Batch Processing**: Handle up to 25 resumes simultaneously
- **Smart Validation**: Automatic resume content validation and quality scoring
- **AI-Powered Analysis**: Ask natural language questions about candidates
- **Intelligent Comparisons**: Compare candidates and get rankings
- **Table Results**: Get structured data in table format for easy analysis
- **Interactive Chat**: Conversational interface with suggested questions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/saswatkumar24/hrhelp.git
   cd hrhelp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and add your Google Gemini API key:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

## 📖 Usage Guide

### Uploading Resumes

1. **Select Files**: Click "Select Resume Files" or drag and drop files
2. **Supported Formats**: PDF, DOCX, ZIP (containing PDFs/DOCX)
3. **File Limits**: Maximum 25 files, 16MB per file
4. **Processing**: The app will extract text and validate content

### Asking Questions

Once resumes are uploaded, you can ask questions like:

- **Experience Queries**:
  - "Who has the most experience?"
  - "Which candidates have more than 5 years of experience?"
  
- **Skills Queries**:
  - "Which candidates know Java?"
  - "Who has experience in machine learning?"
  - "Find candidates with Python skills"

- **Comparison Queries**:
  - "Compare the top 3 candidates"
  - "Who is the best candidate for a senior developer role?"
  - "Rank candidates by their qualifications"

- **General Queries**:
  - "Summarize all candidates"
  - "What skills are most common among candidates?"
  - "Which candidates have a computer science degree?"

### Sample Questions

The interface provides sample questions to get you started:
- Who has the most experience?
- Which candidates know Java?
- Compare the top 3 candidates
- Who has experience in machine learning?

## 🏗️ Project Structure

```
HRHelp/
│
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .env.example         # Environment template
│
├── modules/
│   ├── __init__.py
│   ├── resume_processor.py    # Text extraction from files
│   ├── gemini_analyzer.py     # AI analysis with LangChain
│   └── validation.py          # File and content validation
│
├── templates/
│   ├── base.html             # Base template
│   └── index.html            # Main interface
│
├── static/
│   ├── css/
│   │   └── style.css         # Custom styles
│   └── js/
│       └── app.js            # Frontend JavaScript
│
└── uploads/                  # File upload directory
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `FLASK_SECRET_KEY` | Flask secret key | Auto-generated |
| `FLASK_DEBUG` | Enable debug mode | `True` |
| `MAX_CONTENT_LENGTH` | Max file size (bytes) | `16777216` (16MB) |
| `UPLOAD_FOLDER` | Upload directory | `uploads` |
| `MAX_FILES` | Maximum files allowed | `25` |

### Customization

- **File Types**: Edit `ALLOWED_EXTENSIONS` in `config.py`
- **Upload Limits**: Modify `MAX_FILES` and `MAX_CONTENT_LENGTH`
- **Styling**: Customize `static/css/style.css`
- **AI Prompts**: Edit prompts in `modules/gemini_analyzer.py`

## 🛡️ Security Features

- **File Type Validation**: Only allows safe file formats
- **Size Limits**: Prevents oversized file uploads
- **Content Validation**: Checks if files contain resume-like content
- **Session Management**: Secure session handling
- **Input Sanitization**: Prevents XSS attacks

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main interface |
| `/upload` | POST | Upload and process resumes |
| `/chat` | POST | Send analysis questions |
| `/status` | GET | Check session status |
| `/clear` | GET | Clear current session |
| `/health` | GET | Health check |

## 🧪 Example API Usage

### Upload Files
```bash
curl -X POST http://localhost:8000/upload
  -F "files=@resume1.pdf" \
  -F "files=@resume2.docx"
```

### Ask Question
```bash
curl -X POST http://localhost:8000/chat
  -H "Content-Type: application/json" \
  -d '{"message": "Who has the most experience?"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: Google API key not found
   ```
   Solution: Make sure your `.env` file contains a valid `GOOGLE_API_KEY`

2. **File Upload Fails**
   ```
   Error: File too large
   ```
   Solution: Check file size (max 16MB) or increase `MAX_CONTENT_LENGTH`

3. **No Text Extracted**
   ```
   Warning: Insufficient text extracted
   ```
   Solution: Ensure files contain readable text, not just images

4. **Module Import Error**
   ```
   ModuleNotFoundError: No module named 'langchain_google_genai'
   ```
   Solution: Install dependencies: `pip install -r requirements.txt`

### Debug Mode

Enable debug mode by setting `FLASK_DEBUG=True` in your `.env` file for detailed error messages.

### Logging

Check the console output for detailed logs about file processing and API calls.

## 🚀 Production Deployment

### Deploy to Render.com (Recommended)

This project is configured for easy deployment on Render.com:

1. **Fork this repository** to your GitHub account
2. **Sign up** at [render.com](https://render.com)
3. **Create a new Web Service**
   - Connect your GitHub account
   - Select your forked `hrhelp` repository
   - Render will automatically detect the `render.yaml` configuration
4. **Set environment variables**:
   - `GOOGLE_API_KEY`: Your Google Gemini API key
   - `FLASK_SECRET_KEY`: A random secret string (optional - auto-generated)
5. **Deploy**: Click deploy and wait for the build to complete
6. **Access**: Your app will be available at `https://your-app-name.onrender.com`

### Using Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Environment Setup

For production:
- Set `FLASK_DEBUG=False`
- Use a strong `FLASK_SECRET_KEY`
- Configure proper file upload limits
- Set up reverse proxy (nginx)
- Use HTTPS

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) for the powerful language model
- [LangChain](https://langchain.com/) for the AI framework
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Bootstrap](https://getbootstrap.com/) for the UI components

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing [Issues](../../issues)
3. Create a new [Issue](../../issues/new) if needed

## 🔮 Roadmap

- [ ] Support for more file formats (RTF, TXT)
- [ ] Bulk export of analysis results
- [ ] Advanced filtering and search
- [ ] Integration with ATS systems
- [ ] Multi-language resume support
- [ ] Resume scoring and ranking algorithms
- [ ] Email notification system
- [ ] Admin dashboard for usage analytics

---

**Built with ❤️ for HR professionals**
