from typing import List, Dict, Tuple, Any
import re
import os
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileValidator:
    """Validates uploaded files for resume processing."""
    
    def __init__(self):
        self.max_files = Config.MAX_FILES
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.max_file_size = Config.MAX_CONTENT_LENGTH
    
    def validate_upload(self, files: List) -> Tuple[List[Dict], List[str]]:
        """
        Validate uploaded files.
        
        Args:
            files: List of uploaded file objects
            
        Returns:
            Tuple of (valid_files, validation_errors)
        """
        valid_files = []
        errors = []
        
        # Check number of files
        if len(files) == 0:
            errors.append("No files were uploaded.")
            return valid_files, errors
            
        if len(files) > self.max_files:
            errors.append(f"Too many files uploaded. Maximum allowed: {self.max_files}")
            return valid_files, errors
        
        # Validate each file
        for file in files:
            if file.filename == '':
                errors.append("One or more files have no filename.")
                continue
                
            # Check file extension
            if not Config.allowed_file(file.filename):
                errors.append(f"File '{file.filename}' has unsupported format. "
                            f"Allowed formats: {', '.join(self.allowed_extensions)}")
                continue
            
            # Check file size (if available)
            if hasattr(file, 'content_length') and file.content_length:
                if file.content_length > self.max_file_size:
                    errors.append(f"File '{file.filename}' is too large. "
                                f"Maximum size: {self.max_file_size / (1024*1024):.1f}MB")
                    continue
            
            valid_files.append({
                'file': file,
                'filename': file.filename,
                'size': getattr(file, 'content_length', 0)
            })
        
        if not valid_files and not errors:
            errors.append("No valid files found for processing.")
            
        return valid_files, errors

class ResumeValidator:
    """Advanced validation for resume content."""
    
    def __init__(self):
        self.required_sections = [
            'experience', 'education', 'skills', 'work', 'employment'
        ]
        self.contact_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
            r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b'  # Phone with area code
        ]
    
    def validate_resume_quality(self, resume_data: Dict) -> Dict[str, Any]:
        """
        Perform comprehensive validation of resume content.
        
        Args:
            resume_data: Dictionary containing resume text and metadata
            
        Returns:
            Validation results dictionary
        """
        text = resume_data.get('text', '').lower()
        filename = resume_data.get('filename', 'Unknown')
        word_count = resume_data.get('word_count', 0)
        
        validation_result = {
            'filename': filename,
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': [],
            'sections_found': [],
            'contact_info': {
                'email_found': False,
                'phone_found': False
            },
            'quality_metrics': {
                'word_count': word_count,
                'completeness': 0
            }
        }
        
        # Basic length validation
        if word_count < 50:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Resume is too short (less than 50 words)")
        elif word_count < 100:
            validation_result['warnings'].append("Resume seems quite short for a comprehensive CV")
        
        # Check for resume sections
        sections_found = 0
        for section in self.required_sections:
            if section in text:
                validation_result['sections_found'].append(section)
                sections_found += 1
        
        if sections_found < 2:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Resume doesn't contain enough standard sections")
        elif sections_found < 3:
            validation_result['warnings'].append("Resume could include more standard sections")
        
        validation_result['quality_metrics']['completeness'] = min(100, (sections_found / len(self.required_sections)) * 100)
        
        # Check for contact information
        original_text = resume_data.get('text', '')
        for pattern in self.contact_patterns:
            if re.search(pattern, original_text):
                if '@' in pattern:
                    validation_result['contact_info']['email_found'] = True
                else:
                    validation_result['contact_info']['phone_found'] = True
                break
        
        if not validation_result['contact_info']['email_found'] and not validation_result['contact_info']['phone_found']:
            validation_result['warnings'].append("No contact information detected")
        
        # Quality suggestions
        if word_count > 1000:
            validation_result['suggestions'].append("Consider condensing the resume for better readability")
        elif word_count < 200:
            validation_result['suggestions'].append("Consider adding more detail about experience and skills")
        
        if 'objective' not in text and 'summary' not in text:
            validation_result['suggestions'].append("Consider adding a professional summary or objective")
        
        # No scoring needed - just return validation result
        
        return validation_result
    
    def batch_validate_resumes(self, resumes: List[Dict]) -> Dict[str, Any]:
        """
        Validate multiple resumes and provide batch summary.
        
        Args:
            resumes: List of resume dictionaries
            
        Returns:
            Batch validation results
        """
        results = []
        total_valid = 0
        total_warnings = 0
        total_errors = 0
        
        for resume in resumes:
            validation = self.validate_resume_quality(resume)
            results.append(validation)
            
            if validation['is_valid']:
                total_valid += 1
            total_warnings += len(validation['warnings'])
            total_errors += len(validation['errors'])
        
        batch_summary = {
            'total_resumes': len(resumes),
            'valid_resumes': total_valid,
            'invalid_resumes': len(resumes) - total_valid,
            'total_warnings': total_warnings,
            'total_errors': total_errors,
            'validation_results': results,
            'recommendations': self._generate_batch_recommendations(results)
        }
        
        return batch_summary
    
    def _generate_batch_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations based on batch validation results."""
        recommendations = []
        
        if not results:
            return recommendations
        
        # Analyze common issues
        short_resumes = sum(1 for r in results if r['quality_metrics']['word_count'] < 200)
        missing_contact = sum(1 for r in results if not r['contact_info']['email_found'] and not r['contact_info']['phone_found'])
        invalid_resumes = sum(1 for r in results if not r['is_valid'])
        
        if short_resumes > len(results) * 0.3:
            recommendations.append(f"{short_resumes} resumes appear to be quite short. Consider asking for more detailed CVs.")
        
        if missing_contact > len(results) * 0.2:
            recommendations.append(f"{missing_contact} resumes are missing clear contact information.")
        
        if invalid_resumes > len(results) * 0.2:
            recommendations.append("Some resumes have validation issues. Consider providing clearer submission guidelines.")
        
        if invalid_resumes == 0 and missing_contact < len(results) * 0.1 and short_resumes < len(results) * 0.2:
            recommendations.append("Good overall resume quality. The candidate pool appears well-prepared.")
        
        return recommendations
