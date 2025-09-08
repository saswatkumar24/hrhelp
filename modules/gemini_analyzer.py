from typing import List, Dict, Any
import json
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import google.generativeai as genai
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiResumeAnalyzer:
    """Handles resume analysis using Google Gemini via LangChain."""
    
    def __init__(self):
        """Initialize the Gemini analyzer with API key from config."""
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in your .env file.")
        
        self.llm = GoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        self.resumes_data = []
        self.analysis_cache = {}
        self._last_mentioned_resume = None
        
    def load_resumes(self, resumes: List[Dict]) -> None:
        """Load processed resumes into the analyzer."""
        self.resumes_data = resumes
        self.analysis_cache = {}  # Clear cache when new resumes are loaded
        self._last_mentioned_resume = None  # Clear context when new resumes are loaded
        logger.info(f"Loaded {len(resumes)} resumes for analysis")
        
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze a question about the loaded resumes.
        
        Args:
            question: The question to analyze
            
        Returns:
            Dictionary with analysis results including text response and any tables
        """
        if not self.resumes_data:
            return {
                "response": "No resumes have been uploaded yet. Please upload some resumes first.",
                "table": None,
                "error": "No resumes loaded"
            }
        
        try:
            # Create context from all resumes
            context = self._create_resume_context()
            
            # Determine the type of question and generate appropriate response
            if self._is_comparison_question(question):
                return self._handle_comparison_question(question, context)
            elif self._is_search_question(question):
                return self._handle_search_question(question, context)
            else:
                return self._handle_general_question(question, context)
                
        except Exception as e:
            logger.error(f"Error analyzing question: {str(e)}")
            return {
                "response": f"Sorry, I encountered an error while analyzing your question: {str(e)}",
                "table": None,
                "error": str(e)
            }
    
    def _create_resume_context(self) -> str:
        """Create a structured context from all loaded resumes."""
        context_parts = []
        
        for i, resume in enumerate(self.resumes_data, 1):
            context_parts.append(f"RESUME {i} - {resume['filename']}:")
            context_parts.append(f"File Type: {resume['file_type']}")
            context_parts.append(f"Word Count: {resume['word_count']}")
            context_parts.append("Content:")
            context_parts.append(resume['text'][:2000] + "..." if len(resume['text']) > 2000 else resume['text'])
            context_parts.append("-" * 50)
            
        return "\n".join(context_parts)
    
    def _is_comparison_question(self, question: str) -> bool:
        """Check if the question explicitly requires comparing candidates."""
        comparison_keywords = [
            'compare', 'comparison', 'versus', 'vs', 'better', 'best',
            'rank', 'ranking', 'top 3', 'top 5', 'most qualified', 'most experienced'
        ]
        question_lower = question.lower()
        # Only treat as comparison if explicitly asking for comparison or ranking
        return any(keyword in question_lower for keyword in comparison_keywords) and (
            'compare' in question_lower or 'rank' in question_lower or 'top' in question_lower
        )
    
    def _is_search_question(self, question: str) -> bool:
        """Check if the question is searching for specific skills/criteria."""
        search_keywords = [
            'who', 'which', 'candidates', 'knows', 'has', 'experience in',
            'skilled in', 'proficient', 'familiar with'
        ]
        return any(keyword in question.lower() for keyword in search_keywords)
    
    def _handle_comparison_question(self, question: str, context: str) -> Dict[str, Any]:
        """Handle questions that require comparing candidates."""
        prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
You are an HR assistant analyzing resumes. Based on the resume data provided, answer the comparison question naturally and conversationally.

Question: {question}

Resume Data:
{context}

Provide a clear, direct answer. Only include tables or structured data if the question specifically asks for comparison, ranking, or tabular format. Otherwise, provide a natural conversational response.

Focus on:
- Direct answers to what was asked
- Relevant qualifications and experience
- Brief reasoning when helpful

Avoid unnecessary scores, ratings, or complex formatting unless specifically requested.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(question=question, context=context)
        
        # Track the mentioned candidate for context
        self._update_context_from_response(response, question)
        
        # Parse response to extract table data
        table_data = self._extract_table_from_response(response)
        
        return {
            "response": response,
            "table": table_data,
            "question_type": "comparison"
        }
    
    def _handle_search_question(self, question: str, context: str) -> Dict[str, Any]:
        """Handle questions searching for candidates with specific skills."""
        prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
You are an HR assistant analyzing resumes. Based on the resume data provided, find candidates that match the search criteria.

Question: {question}

Resume Data:
{context}

Provide a natural, conversational response. List the matching candidates and briefly explain their relevant qualifications. Only create tables if the question specifically asks for structured data or comparisons.

Focus on:
- Which candidates match the criteria
- Their relevant experience or skills
- Brief context about their qualifications

Keep the response conversational and avoid unnecessary formatting, scores, or ratings.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(question=question, context=context)
        
        # Track the mentioned candidate for context
        self._update_context_from_response(response, question)
        
        table_data = self._extract_table_from_response(response)
        
        return {
            "response": response,
            "table": table_data,
            "question_type": "search"
        }
    
    def _handle_general_question(self, question: str, context: str) -> Dict[str, Any]:
        """Handle general questions about the resumes."""
        
        # Check if user is asking for file downloads
        download_keywords = ['download', 'file', 'original', 'pdf', 'docx', 'resume file']
        if any(keyword in question.lower() for keyword in download_keywords):
            # Try to identify specific person/candidate mentioned in the question
            specific_resume = self._find_specific_resume_from_question(question)
            
            if specific_resume:
                # Provide download link for specific person
                download_response = f"Here's the download link for {specific_resume['candidate_name']}'s resume:\n\n• {specific_resume['filename']}\n\nThis is the resume file for the candidate you mentioned."
                return {
                    "response": download_response,
                    "table": None,
                    "question_type": "download",
                    "specific_file": specific_resume['filename']
                }
            else:
                # Provide all files if no specific person mentioned
                file_list = "\n".join([f"• {resume['filename']}" for resume in self.resumes_data])
                download_response = f"I can help you access the original resume files! Here are all the uploaded files:\n\n{file_list}\n\nWhich specific resume would you like to download?"
                
                return {
                    "response": download_response,
                    "table": None,
                    "question_type": "download"
                }
        
        prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
You are an HR assistant analyzing resumes. Based on the resume data provided, answer the question in a natural, conversational way.

Question: {question}

Resume Data:
{context}

Provide a clear, direct answer that's helpful for HR decision-making. Keep it conversational and professional. Only use structured formats like tables if the question specifically asks for organized data or comparisons.

Focus on giving practical, actionable information without unnecessary complexity.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(question=question, context=context)
        
        return {
            "response": response,
            "table": None,
            "question_type": "general"
        }
    
    def _extract_table_from_response(self, response: str) -> List[Dict]:
        """Extract table data from the LLM response only if explicitly formatted as a table."""
        # Only look for tables if the response contains clear table formatting
        if '|' not in response or 'table' not in response.lower():
            return None
            
        lines = response.split('\n')
        table_data = []
        
        # Look for table-like structures with clear formatting
        in_table = False
        headers = []
        
        for line in lines:
            line = line.strip()
            # Only start table parsing if there's explicit table formatting
            if ('table' in line.lower() or 'comparison' in line.lower()) and '|' in line:
                in_table = True
                continue
            elif in_table and '|' in line and len(line.split('|')) >= 3:
                parts = [part.strip() for part in line.split('|') if part.strip()]
                if len(parts) >= 2:
                    if not headers:
                        headers = parts
                    else:
                        row_dict = {}
                        for i, value in enumerate(parts):
                            if i < len(headers):
                                row_dict[headers[i]] = value
                        if row_dict:
                            table_data.append(row_dict)
            elif in_table and (line == '' or not '|' in line):
                break
                
        # Only return table data if we found a substantial table
        return table_data if len(table_data) >= 2 else None
    
    def get_resume_summary(self) -> Dict[str, Any]:
        """Get a summary of all loaded resumes."""
        if not self.resumes_data:
            return {"summary": "No resumes loaded", "count": 0}
        
        summary = {
            "count": len(self.resumes_data),
            "file_types": {},
            "total_words": 0,
            "avg_words": 0
        }
        
        for resume in self.resumes_data:
            file_type = resume['file_type']
            summary['file_types'][file_type] = summary['file_types'].get(file_type, 0) + 1
            summary['total_words'] += resume['word_count']
        
        summary['avg_words'] = summary['total_words'] // summary['count'] if summary['count'] > 0 else 0
        
        return summary
    
    def _find_specific_resume_from_question(self, question: str) -> Dict:
        """Try to identify which specific resume the user is asking about based on context."""
        question_lower = question.lower()
        
        # Extract potential names from filenames and match against question
        for resume in self.resumes_data:
            filename = resume['filename']
            
            # Extract candidate name from filename (common patterns)
            candidate_names = self._extract_candidate_names(filename)
            
            # Check if any extracted name appears in the question
            for name in candidate_names:
                if name.lower() in question_lower:
                    return {
                        'filename': filename,
                        'candidate_name': name,
                        'resume_data': resume
                    }
        
        # If no name match, try to use pronouns with context from recent analysis
        if any(pronoun in question_lower for pronoun in ['his', 'her', 'their', 'this person', 'that candidate']):
            # This is a contextual reference - we need to track the last mentioned candidate
            # For now, we'll use a simple heuristic based on the most recently discussed resume
            if hasattr(self, '_last_mentioned_resume') and self._last_mentioned_resume:
                return self._last_mentioned_resume
        
        return None
    
    def _extract_candidate_names(self, filename: str) -> List[str]:
        """Extract possible candidate names from filename."""
        # Remove file extension
        name_part = filename.rsplit('.', 1)[0]
        logger.info(f"Extracting names from filename: {filename} -> {name_part}")
        
        candidates = []
        
        # Pattern 1: FirstName_LastName_extras (like "saswat_11y")
        if '_' in name_part:
            parts = name_part.split('_')
            for part in parts:
                # Skip common non-name patterns
                if (part.lower() not in ['resume', 'cv', 'updated', 'final', 'new'] and 
                    not part.isdigit() and 
                    not part.endswith('y') and  # Skip "11y" type patterns
                    len(part) > 1):
                    candidates.append(part.lower())  # Keep lowercase for matching
        
        # Pattern 2: FirstName LastName (space separated)
        elif ' ' in name_part:
            parts = name_part.split(' ')
            for part in parts:
                if (part.lower() not in ['resume', 'cv', 'updated', 'final', 'new'] and 
                    not part.isdigit() and len(part) > 1):
                    candidates.append(part.lower())
        
        # Pattern 3: CamelCase or single name
        else:
            # Remove common keywords first
            clean_name = name_part.lower()
            for keyword in ['resume', 'cv', 'resumeee']:  # Note: "resumeee" pattern
                clean_name = clean_name.replace(keyword, '')
            clean_name = clean_name.strip('_-')
            
            if clean_name and len(clean_name) > 1 and not clean_name.isdigit():
                candidates.append(clean_name)
        
        logger.info(f"Extracted candidates: {candidates}")
        return candidates
    
    def _update_context_from_response(self, response: str, question: str) -> None:
        """Update context tracking based on AI response and question."""
        response_lower = response.lower()
        question_lower = question.lower()
        
        logger.info(f"Updating context from response: {response[:100]}...")
        logger.info(f"Question was: {question}")
        
        # First try to identify from the response text
        for resume in self.resumes_data:
            filename = resume['filename']
            candidate_names = self._extract_candidate_names(filename)
            
            # Check if any candidate name appears in the response
            for name in candidate_names:
                if name in response_lower:
                    logger.info(f"Found candidate {name} in response, setting as last mentioned")
                    self._last_mentioned_resume = {
                        'filename': filename,
                        'candidate_name': name.capitalize(),
                        'resume_data': resume
                    }
                    return
        
        # If no direct name match, analyze the response pattern
        # Look for patterns like "[Name] has the most experience" or "Based on... [Name] boasts"
        import re
        
        # Pattern: "[Name] has" or "[Name] boasts" - extract the name before these verbs
        name_patterns = [
            r'([A-Za-z]+(?:\s+[A-Za-z]+)?(?:\s+[A-Za-z]+)?)\s+(?:has|boasts|shows|demonstrates)\s+(?:the\s+)?(?:most|highest|best)',
            r'([A-Za-z]+(?:\s+[A-Za-z]+)?(?:\s+[A-Za-z]+)?)\s+(?:is|appears|seems)\s+(?:the\s+)?(?:most|best)',
            r'(?:Based on.*?)([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:has|boasts)'
        ]
        
        for pattern in name_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                potential_name = match.group(1).strip().lower()
                logger.info(f"Found potential name from pattern: {potential_name}")
                
                # Try to match this with our candidate names
                for resume in self.resumes_data:
                    candidate_names = self._extract_candidate_names(resume['filename'])
                    for name in candidate_names:
                        if name in potential_name or potential_name in name:
                            logger.info(f"Matched pattern name {potential_name} with candidate {name}")
                            self._last_mentioned_resume = {
                                'filename': resume['filename'],
                                'candidate_name': name.capitalize(),
                                'resume_data': resume
                            }
                            return
        
        logger.info("No specific candidate identified from response")
