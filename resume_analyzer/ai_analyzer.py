"""
AI-powered deep analysis module for resume evaluation
Provides comprehensive AI insights when API key is available
"""

from openai import OpenAI
import logging
from .config import ATS_KEYWORDS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIResumeAnalyzer:
    """AI-powered comprehensive resume analysis using OpenAI GPT models"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.ats_keywords = ATS_KEYWORDS
        self.client = None
        if api_key:
            self.client = OpenAI(api_key=api_key)
    
    def set_api_key(self, api_key):
        """Set OpenAI API key for AI analysis"""
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def get_comprehensive_ai_analysis(self, resume_text, target_role=None):
        """
        Get comprehensive AI analysis with detailed insights
        
        Args:
            resume_text (str): Resume text content
            target_role (str): Target job role for focused analysis
            
        Returns:
            str: Comprehensive AI analysis with actionable insights
        """
        if not self.client:
            return "AI analysis requires OpenAI API key. Please configure your API key to access detailed AI insights."
        
        try:
            prompt = self._create_comprehensive_analysis_prompt(resume_text, target_role)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_role_specific_system_prompt(target_role)
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.4
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.info(f"Generated targeted {target_role} analysis successfully")
            return analysis
            
        except Exception as e:
            error_msg = f"Role-specific AI analysis unavailable: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_improvement_recommendations(self, resume_text, weaknesses_analysis):
        """
        Get AI-powered improvement recommendations based on identified weaknesses
        
        Args:
            resume_text (str): Resume text content
            weaknesses_analysis (list): List of identified weaknesses
            
        Returns:
            str: AI-generated improvement recommendations
        """
        if not self.client:
            return "AI improvement recommendations require OpenAI API key."
        
        try:
            prompt = self._create_improvement_prompt(resume_text, weaknesses_analysis)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert career coach specializing in resume optimization and professional development. Provide specific, actionable improvement recommendations."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            recommendations = response.choices[0].message.content.strip()
            logger.info("Generated AI improvement recommendations successfully")
            return recommendations
            
        except Exception as e:
            error_msg = f"AI improvement recommendations unavailable: {str(e)}"
            logger.error(error_msg)
            return error_msg

    # ... (keep all your existing prompt creation methods as they are) ...

    def validate_api_connection(self):
        """
        Validate OpenAI API connection and key
        
        Returns:
            tuple: (is_valid, message)
        """
        if not self.api_key:
            return False, "No API key provided"
        
        try:
            # Simple test call to validate the API key
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return True, "API key validated successfully"
        except Exception as e:
            error_type = type(e).__name__
            if "AuthenticationError" in error_type:
                return False, "Invalid API key - please check your OpenAI API key"
            elif "RateLimitError" in error_type:
                return False, "API rate limit exceeded - please try again later"
            elif "APIError" in error_type:
                return False, f"API error: {str(e)}"
            else:
                return False, f"Connection error: {str(e)}"
    
    def get_analysis_cost_estimate(self, resume_text, target_role=None):
        """
        Estimate cost for AI analysis based on token usage
        
        Args:
            resume_text (str): Resume text content
            target_role (str): Optional target role
            
        Returns:
            dict: Cost estimation details
        """
        # Rough token estimation (1 token ≈ 4 characters)
        resume_tokens = len(resume_text) // 4
        prompt_tokens = 1000  # Average prompt size
        response_tokens = 1500  # Average response size
        
        total_tokens = resume_tokens + prompt_tokens + response_tokens
        
        # GPT-3.5-turbo pricing (approximate)
        cost_per_1k_tokens = 0.002
        estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens

        analysis_types = ["Comprehensive Analysis"]
        if target_role:
            analysis_types.append("Role-Specific Analysis")
            estimated_cost *= 1.5  # Additional cost for targeted analysis

        return {
            'estimated_tokens': total_tokens,
            'estimated_cost_usd': round(estimated_cost, 4),
            'analysis_types': analysis_types,
            'cost_breakdown': {
                'input_tokens': resume_tokens + prompt_tokens,
                'output_tokens': response_tokens,
                'total_tokens': total_tokens
            }
        }


