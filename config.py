import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Google Gemini API settings
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    # Upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_FILES = int(os.environ.get('MAX_FILES', 25))
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'zip'}
    
    # Application info
    APP_NAME = os.environ.get('APP_NAME', 'HR Resume Analyzer')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
