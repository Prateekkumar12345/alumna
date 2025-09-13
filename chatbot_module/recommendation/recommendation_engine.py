from typing import Dict, List, Any
from .college_repository import CollegeRepository

class RecommendationEngine:
    """Generates college recommendations based on student profile and context"""
    
    def __init__(self):
        self.college_repository = CollegeRepository()
    
    def generate_recommendations(self, criteria: Dict[str, Any], profile: Any) -> List[Dict]:
        """
        Generate college recommendations based on criteria and student profile
        """
        # Fetch colleges based on criteria
        colleges = self.college_repository.search_colleges(
            field_keywords=criteria.get("field_keywords"),
            location=criteria.get("location"),
            college_type=criteria.get("college_type")
        )
        
        # If no specific criteria, get all colleges
        if not colleges:
            colleges = self.college_repository.fetch_all_colleges()
        
        # Score and filter colleges
        scored_colleges = []
        for college in colleges:
            score, reasons = self._score_college(college, criteria, profile)
            
            if score > 15:  # Minimum threshold
                scored_colleges.append({
                    "name": college['name'],
                    "location": college['location'],
                    "fees": college.get('fees', 0),
                    "match_score": min(score, 100.0),
                    "match_reasons": reasons or ["Good overall fit based on your profile"],
                    "type": college.get('type', 'General'),
                    "admission": college.get('admission', 'Various entrance exams'),
                    "highlights": college.get('highlights', [])[:3],
                    "website": college.get('website'),
                    "contact": college.get('contact'),
                    "email": college.get('email'),
                    "scholarship": college.get('scholarship'),
                    "affiliation": college.get('affiliation')
                })
        
        # Sort by match score and return top recommendations
        scored_colleges.sort(key=lambda x: x['match_score'], reverse=True)
        return scored_colleges[:10] if scored_colleges else []
    
    def _score_college(self, college: Dict, criteria: Dict, profile: Any) -> tuple:
        """Score a college based on how well it matches criteria and profile"""
        score = 0
        reasons = []
        
        # Check field alignment
        field_keywords = criteria.get("field_keywords", [])
        if field_keywords:
            college_streams = college.get('streams', [])
            college_courses = college.get('courses', [])
            
            field_match = False
            # Check streams
            if college_streams:
                field_match = any(
                    any(pref.lower() in stream.lower() for stream in college_streams)
                    for pref in field_keywords
                )
            
            # Also check in courses data
            if not field_match and college_courses:
                for course in college_courses:
                    if isinstance(course, dict):
                        course_category = course.get('Category', '').lower()
                        if any(pref.lower() in course_category for pref in field_keywords):
                            field_match = True
                            break
            
            if field_match:
                score += 50
                reasons.append(f"Offers programs in {', '.join(field_keywords)}")
        
        # Location preference
        location = criteria.get("location")
        if location:
            if location.lower() in college.get('location', '').lower():
                score += 25
                reasons.append("Preferred location")
        
        # Budget constraint
        budget = criteria.get("budget_constraint")
        college_fees = college.get('fees', 0)
        if budget and college_fees > 0:
            if college_fees <= budget:
                score += 20
                reasons.append("Within your budget")
            elif college_fees <= budget * 1.5:  # Slightly over budget
                score += 10
                reasons.append("Slightly over budget but good value")
            else:
                score -= 10  # Penalize colleges way over budget
        
        # Quality indicators
        if college.get('affiliation'):
            score += 10
            
        if college.get('scholarship') and college.get('scholarship').lower() != "n/a":
            score += 15
            reasons.append("Scholarships available")
            
        if college.get('website'):
            score += 5
        
        # Add base score for having complete information
        score += len(college.get('highlights', [])) * 3
        
        return score, reasons