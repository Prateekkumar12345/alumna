import re
from typing import Dict, Any, List
from datetime import datetime
from chatbot_module.models import DynamicStudentProfile

class ContextAnalyzer:
    """Analyzes conversation context to determine when to recommend colleges"""
    
    def __init__(self):
        self.context_triggers = [
            # Academic context triggers
            r"(best|good|top).*(college|university|institute)",
            r"(study|pursue|take).*(engineering|medical|mba|degree)",
            r"(admission|apply|application).*(college|university)",
            r"(career|future|job).*(path|option|choice)",
            r"(interested|passionate|like).*(field|subject|domain)",
            
            # Location context triggers
            r"(college|study).*(delhi|mumbai|bangalore|pune|hyderabad|chennai|kolkata|indore)",
            
            # Financial context triggers
            r"(fee|cost|expense|budget).*(college|education)",
            r"(affordable|expensive|cheap).*(college|option)",
            
            # Comparative context triggers
            r"(compare|difference).*(college|university|institute)",
            r"(which one|what).*(better|best|good)",
            
            # Direct inquiry triggers (weaker signals)
            r"(suggest|recommend|advise).*",
            r"(option|choice|alternative).*",
            r"(what|how).*(choose|select|pick)"
        ]
        
        self.compiled_triggers = [re.compile(pattern, re.IGNORECASE) for pattern in self.context_triggers]
    
    def should_recommend_colleges(self, message: str, conversation_history: List, 
                                 student_profile: DynamicStudentProfile) -> bool:
        """
        Determine if college recommendations should be provided based on context
        """
        message_lower = message.lower()
        
        # Check for explicit recommendation requests
        if any(word in message_lower for word in ["recommend", "suggest", "advise", "options"]):
            return True
        
        # Check for context patterns
        for pattern in self.compiled_triggers:
            if pattern.search(message_lower):
                return True
        
        # Check if we have sufficient profile information
        if self._has_sufficient_profile_info(student_profile):
            # If we have good profile info and the conversation is about education/career
            education_keywords = ["college", "university", "study", "degree", "career", "future"]
            if any(keyword in message_lower for keyword in education_keywords):
                return True
        
        # Check conversation history for education context
        if self._has_education_context(conversation_history):
            return True
            
        return False
    
    def _has_sufficient_profile_info(self, profile: DynamicStudentProfile) -> bool:
        """Check if we have sufficient information to make recommendations"""
        has_academic_info = (hasattr(profile, 'scores') and profile.scores and 
                            (profile.scores.get('percentage') or profile.scores.get('percentile')))
        has_field_preference = (hasattr(profile, 'preferred_fields') and 
                               profile.preferred_fields and len(profile.preferred_fields) > 0)
        
        return has_academic_info and has_field_preference
    
    def _has_education_context(self, conversation_history: List) -> bool:
        """Check if recent conversation has education context"""
        if not conversation_history or len(conversation_history) < 2:
            return False
        
        # Check last few messages for education context
        recent_messages = conversation_history[-4:]  # Last 2 exchanges
        education_keywords = ["college", "university", "study", "degree", "career", "education"]
        
        for message in recent_messages:
            content = message.get('content', '').lower()
            if any(keyword in content for keyword in education_keywords):
                return True
                
        return False
    
    def extract_recommendation_criteria(self, message: str, student_profile: DynamicStudentProfile) -> Dict[str, Any]:
        """
        Extract specific criteria for college recommendations from message and profile
        """
        criteria = {
            "field_keywords": [],
            "location": None,
            "college_type": None,
            "budget_constraint": None
        }
        
        message_lower = message.lower()
        
        # Extract field preferences from message or use profile
        field_keywords = self._extract_fields_from_message(message_lower)
        if field_keywords:
            criteria["field_keywords"] = field_keywords
        elif hasattr(student_profile, 'preferred_fields') and student_profile.preferred_fields:
            criteria["field_keywords"] = student_profile.preferred_fields
        
        # Extract location from message or use profile
        location = self._extract_location_from_message(message_lower)
        if location:
            criteria["location"] = location
        elif hasattr(student_profile, 'location_preference') and student_profile.location_preference:
            criteria["location"] = student_profile.location_preference.lower()
        
        # Extract college type from message
        college_type = self._extract_college_type_from_message(message_lower)
        if college_type:
            criteria["college_type"] = college_type
        
        # Extract budget constraints
        budget = self._extract_budget_from_message(message_lower)
        if budget:
            criteria["budget_constraint"] = budget
        elif hasattr(student_profile, 'budget') and student_profile.budget:
            criteria["budget_constraint"] = student_profile.budget
        
        return criteria
    
    def _extract_fields_from_message(self, message: str) -> List[str]:
        """Extract field interests from message"""
        fields = []
        field_mappings = {
            "computer": "Computer Science",
            "programming": "Computer Science",
            "software": "Computer Science",
            "tech": "Technology",
            "it": "Information Technology",
            "medical": "Medicine",
            "doctor": "Medicine",
            "healthcare": "Medicine",
            "mbbs": "Medicine",
            "business": "Business",
            "management": "Business",
            "mba": "Business",
            "finance": "Business",
            "marketing": "Business",
            "engineering": "Engineering",
            "arts": "Arts",
            "science": "Science",
            "commerce": "Commerce",
            "law": "Law",
            "architecture": "Architecture"
        }
        
        for keyword, field in field_mappings.items():
            if keyword in message and field not in fields:
                fields.append(field)
                
        return fields
    
    def _extract_location_from_message(self, message: str) -> str:
        """Extract location preference from message"""
        locations = ["delhi", "mumbai", "bangalore", "pune", "hyderabad", 
                    "chennai", "kolkata", "indore", "ahmedabad"]
        
        for location in locations:
            if location in message:
                return location
                
        return None
    
    def _extract_college_type_from_message(self, message: str) -> str:
        """Extract college type preference from message"""
        if "government" in message or "govt" in message:
            return "government"
        elif "private" in message:
            return "private"
        elif "deemed" in message:
            return "deemed"
        elif "iit" in message:
            return "iit"
        elif "nit" in message:
            return "nit"
        elif "iim" in message:
            return "iim"
            
        return None
    
    def _extract_budget_from_message(self, message: str) -> float:
        """Extract budget information from message"""
        budget_match = re.search(r"(\d+(\.\d+)?)\s*(lakh|lakhs|₹)", message)
        if budget_match:
            amount = float(budget_match.group(1))
            if "lakh" in budget_match.group(3):
                amount *= 100000
            return amount
                
        return None