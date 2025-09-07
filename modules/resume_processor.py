import os
import zipfile
import tempfile
from typing import List, Dict, Tuple
import PyPDF2
from docx import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeProcessor:
    """Handles extraction of text from resume files (PDF, DOCX, ZIP)."""
    
    def __init__(self):
        self.supported_extensions = {'.pdf', '.docx'}
        
    def process_files(self, file_paths: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Process multiple resume files and extract text.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Tuple of (processed_resumes, errors)
        """
        processed_resumes = []
        errors = []
        
        for file_path in file_paths:
            try:
                if file_path.lower().endswith('.zip'):
                    # Handle ZIP files
                    zip_results, zip_errors = self._process_zip_file(file_path)
                    processed_resumes.extend(zip_results)
                    errors.extend(zip_errors)
                else:
                    # Handle individual files
                    result = self._process_single_file(file_path)
                    if result:
                        processed_resumes.append(result)
                    else:
                        errors.append(f"Failed to process: {os.path.basename(file_path)}")
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                errors.append(f"Error processing {os.path.basename(file_path)}: {str(e)}")
                
        return processed_resumes, errors
    
    def _process_zip_file(self, zip_path: str) -> Tuple[List[Dict], List[str]]:
        """Extract and process files from a ZIP archive."""
        processed_files = []
        errors = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Create temporary directory for extraction
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Process each extracted file
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_ext = os.path.splitext(file)[1].lower()
                            
                            if file_ext in self.supported_extensions:
                                result = self._process_single_file(file_path)
                                if result:
                                    # Update filename to show it came from ZIP
                                    result['filename'] = f"{os.path.basename(zip_path)}/{file}"
                                    processed_files.append(result)
                                else:
                                    errors.append(f"Failed to process: {file} from {os.path.basename(zip_path)}")
                            
        except Exception as e:
            logger.error(f"Error processing ZIP file {zip_path}: {str(e)}")
            errors.append(f"Error processing ZIP file {os.path.basename(zip_path)}: {str(e)}")
            
        return processed_files, errors
    
    def _process_single_file(self, file_path: str) -> Dict:
        """Process a single resume file and extract text."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            
            if file_ext == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_ext == '.docx':
                text = self._extract_docx_text(file_path)
            else:
                return None
                
            if text and len(text.strip()) > 100:  # Basic validation
                return {
                    'filename': filename,
                    'text': text.strip(),
                    'word_count': len(text.split()),
                    'file_type': file_ext[1:].upper()
                }
            else:
                logger.warning(f"Insufficient text extracted from {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return None
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF text from {pdf_path}: {str(e)}")
            raise
            
        return text
    
    def _extract_docx_text(self, docx_path: str) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = Document(docx_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"Error extracting DOCX text from {docx_path}: {str(e)}")
            raise
            
        return text
    
    def validate_resume_content(self, text: str, filename: str) -> Tuple[bool, List[str]]:
        """
        Validate if the extracted text appears to be a resume.
        
        Args:
            text: Extracted text from file
            filename: Name of the file
            
        Returns:
            Tuple of (is_valid, validation_messages)
        """
        validation_messages = []
        is_valid = True
        
        # Convert to lowercase for checking
        text_lower = text.lower()
        
        # Check minimum length
        if len(text.strip()) < 100:
            is_valid = False
            validation_messages.append("Document is too short to be a resume")
            
        # Check for resume-related keywords
        resume_keywords = [
            'experience', 'education', 'skills', 'work', 'employment',
            'job', 'position', 'university', 'college', 'degree',
            'certification', 'project', 'achievement', 'responsibility'
        ]
        
        keyword_matches = sum(1 for keyword in resume_keywords if keyword in text_lower)
        
        if keyword_matches < 3:
            is_valid = False
            validation_messages.append("Document doesn't contain enough resume-related keywords")
        else:
            validation_messages.append(f"Found {keyword_matches} resume-related keywords")
            
        # Check for contact information patterns
        has_email = '@' in text and '.' in text
        has_phone = any(char.isdigit() for char in text)
        
        if not (has_email or has_phone):
            validation_messages.append("Warning: No contact information detected")
        else:
            validation_messages.append("Contact information found")
            
        # Additional checks
        if len(text.split()) < 50:
            is_valid = False
            validation_messages.append("Document has too few words for a resume")
        else:
            validation_messages.append(f"Document contains {len(text.split())} words")
            
        return is_valid, validation_messages
