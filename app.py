from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from config import Config
from modules.resume_processor import ResumeProcessor
from modules.gemini_analyzer import GeminiResumeAnalyzer
from modules.validation import FileValidator, ResumeValidator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
resume_processor = ResumeProcessor()
gemini_analyzer = GeminiResumeAnalyzer()
file_validator = FileValidator()
resume_validator = ResumeValidator()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Main page with file upload and chat interface."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and process resumes."""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            })
        
        files = request.files.getlist('files')
        
        # Validate files
        valid_files, validation_errors = file_validator.validate_upload(files)
        
        if validation_errors and not valid_files:
            return jsonify({
                'success': False,
                'error': 'File validation failed',
                'errors': validation_errors
            })
        
        # Save files and get paths
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        file_paths = []
        saved_files = []
        
        for file_data in valid_files:
            file = file_data['file']
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_folder, filename)
            file.save(file_path)
            file_paths.append(file_path)
            saved_files.append(filename)
        
        # Process resumes
        processed_resumes, processing_errors = resume_processor.process_files(file_paths)
        
        if not processed_resumes:
            return jsonify({
                'success': False,
                'error': 'No resumes could be processed',
                'errors': processing_errors
            })
        
        # Validate resume content
        validation_summary = resume_validator.batch_validate_resumes(processed_resumes)
        
        # Load resumes into analyzer
        gemini_analyzer.load_resumes(processed_resumes)
        
        # Store session data
        session['session_id'] = session_id
        session['resumes_loaded'] = len(processed_resumes)
        
        # Prepare response
        response_data = {
            'success': True,
            'session_id': session_id,
            'files_uploaded': len(saved_files),
            'resumes_processed': len(processed_resumes),
            'validation_summary': {
                'total_resumes': validation_summary['total_resumes'],
                'valid_resumes': validation_summary['valid_resumes'],
                'invalid_resumes': validation_summary['invalid_resumes'],
                'recommendations': validation_summary['recommendations']
            },
            'processed_files': [r['filename'] for r in processed_resumes]
        }
        
        if validation_errors:
            response_data['warnings'] = validation_errors
        
        if processing_errors:
            response_data['processing_errors'] = processing_errors
        
        logger.info(f"Successfully processed {len(processed_resumes)} resumes for session {session_id}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in upload_files: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and analyze resumes."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            })
        
        message = data['message'].strip()
        if not message:
            return jsonify({
                'success': False,
                'error': 'Empty message'
            })
        
        # Check if resumes are loaded
        if 'session_id' not in session or not session.get('resumes_loaded', 0):
            return jsonify({
                'success': False,
                'error': 'No resumes loaded. Please upload resumes first.'
            })
        
        # Analyze the question
        analysis_result = gemini_analyzer.analyze_question(message)
        
        if 'error' in analysis_result:
            return jsonify({
                'success': False,
                'error': analysis_result['error']
            })
        
        # Format response
        response_data = {
            'success': True,
            'response': analysis_result['response'],
            'question_type': analysis_result.get('question_type', 'general'),
            'table': analysis_result.get('table'),
            'timestamp': None  # Frontend will add timestamp
        }
        
        logger.info(f"Processed chat query for session {session.get('session_id')}: {message[:50]}...")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing your question: {str(e)}'
        })

@app.route('/status')
def status():
    """Get current session status."""
    try:
        session_id = session.get('session_id')
        resumes_loaded = session.get('resumes_loaded', 0)
        
        if session_id and resumes_loaded:
            summary = gemini_analyzer.get_resume_summary()
            return jsonify({
                'success': True,
                'session_active': True,
                'session_id': session_id,
                'resumes_loaded': resumes_loaded,
                'summary': summary
            })
        else:
            return jsonify({
                'success': True,
                'session_active': False,
                'resumes_loaded': 0
            })
            
    except Exception as e:
        logger.error(f"Error in status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/clear')
def clear_session():
    """Clear current session data."""
    try:
        session_id = session.get('session_id')
        if session_id:
            # Clean up uploaded files
            session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
            if os.path.exists(session_folder):
                import shutil
                shutil.rmtree(session_folder)
        
        # Clear session
        session.clear()
        
        # Reset analyzer
        gemini_analyzer.resumes_data = []
        gemini_analyzer.analysis_cache = {}
        
        return jsonify({
            'success': True,
            'message': 'Session cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Test Gemini connection
        test_analyzer = GeminiResumeAnalyzer()
        
        return jsonify({
            'status': 'healthy',
            'gemini_configured': bool(Config.GOOGLE_API_KEY),
            'upload_folder': os.path.exists(app.config['UPLOAD_FOLDER'])
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size allowed is {Config.MAX_CONTENT_LENGTH / (1024*1024):.1f}MB'
    }), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again.'
    }), 500

if __name__ == '__main__':
    print(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Max files: {Config.MAX_FILES}")
    print(f"Gemini API configured: {bool(Config.GOOGLE_API_KEY)}")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=8000)
