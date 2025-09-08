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
        
    def load_resumes(self, resumes: List[Dict]) -> None:
        """Load processed resumes into the analyzer."""
        self.resumes_data = resumes
        self.analysis_cache = {}  # Clear cache when new resumes are loaded
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
        
        table_data = self._extract_table_from_response(response)
        
        return {
            "response": response,
            "table": table_data,
            "question_type": "search"
        }
    
    def _handle_general_question(self, question: str, context: str) -> Dict[str, Any]:
        """Handle general questions about the resumes."""
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
