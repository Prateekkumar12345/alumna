import json
import logging
import re
from typing import Dict, List, Any
from sqlalchemy import create_engine, text
from chatbot_module.config import DATABASE_URI

class CollegeRepository:
    """Handles all database operations for colleges"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URI)
    
    def fetch_all_colleges(self) -> List[Dict]:
        """Fetch all colleges from PostgreSQL database"""
        try:
            query = """
            SELECT
                College_ID,
                College_Name,
                Name,
                Type,
                Affiliation,
                Location,
                Website,
                Contact,
                Email,
                Courses,
                Scholarship,
                Admission_Process
            FROM college
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                colleges = []
                
                rows = result.fetchall()
                column_names = [
                    'College_ID', 'College_Name', 'Name', 'Type', 'Affiliation', 'Location',
                    'Website', 'Contact', 'Email', 'Courses', 'Scholarship', 'Admission_Process'
                ]
                
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    college_data = self._format_college_data(row_dict)
                    colleges.append(college_data)
                
                return colleges
                
        except Exception as e:
            logging.error(f"Error fetching colleges from database: {e}")
            return []
    
    def search_colleges(self, field_keywords=None, location=None, college_type=None) -> List[Dict]:
        """Search colleges based on specific criteria"""
        try:
            query = "SELECT * FROM college WHERE 1=1"
            params = {}
            logging.info(f"Location: {location}, College Type: {college_type}, Field Keywords: {field_keywords}")
            
            if field_keywords:
                query += " AND (LOWER(courses::text) LIKE :field_keyword OR LOWER(type) LIKE :field_keyword)"
                keyword = field_keywords[0].lower()
                params['field_keyword'] = f'%{keyword}%'
            
            if location:
                query += " AND LOWER(location) LIKE :location"
                params['location'] = f'%{location.lower()}%'
            
            if college_type:
                query += " AND LOWER(type) LIKE :college_type"
                params['college_type'] = f'%{college_type.lower()}%'
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                colleges = []
                
                for row in result:
                    row_dict = {column: getattr(row, column) for column in row._fields}
                    college_data = self._format_college_data(row_dict)
                    colleges.append(college_data)
                
                return colleges
                
        except Exception as e:
            logging.error(f"Error searching colleges: {e}")
            return []
    
    def _format_college_data(self, row_dict: Dict) -> Dict:
        """Format college data from database row"""
        courses_data = []
        if row_dict.get('Courses'):
            try:
                if isinstance(row_dict['Courses'], str):
                    courses_data = json.loads(row_dict['Courses'])
                else:
                    courses_data = row_dict['Courses']
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error decoding courses data for college {row_dict.get('College_ID')}: {e}")
                courses_data = []
        
        streams = []
        specialties = []
        if courses_data:
            for course in courses_data:
                if isinstance(course, dict):
                    category = course.get('Category', '')
                    if category:
                        if category not in streams:
                            streams.append(category)
                            specialties.append(category)
        
        return {
            "id": row_dict.get('College_ID'),
            "name": row_dict.get('College_Name') or row_dict.get('Name'),
            "location": row_dict.get('Location') or "Not specified",
            "type": row_dict.get('Type') or "General",
            "affiliation": row_dict.get('Affiliation') or "Not specified",
            "website": row_dict.get('Website'),
            "contact": row_dict.get('Contact'),
            "email": row_dict.get('Email'),
            "courses": courses_data,
            "streams": streams,
            "specialties": specialties,
            "admission": row_dict.get('Admission_Process') or "Various entrance exams",
            "scholarship": row_dict.get('Scholarship') or "Available",
            "fees": self._extract_fees_from_courses(courses_data),
            "highlights": self._generate_highlights(row_dict)
        }
    
    def _extract_fees_from_courses(self, courses_data) -> int:
        """Extract average fees from courses data"""
        if not courses_data:
            return 0
        
        total_fees = 0
        valid_courses = 0
        
        for course in courses_data:
            if isinstance(course, dict) and 'Fees' in course:
                fees_str = str(course['Fees']).lower()
                numbers = re.findall(r'\d+', fees_str)
                if numbers:
                    fee_amount = int(numbers[0])
                    if fee_amount < 1000:
                        fee_amount *= 1000
                    total_fees += fee_amount
                    valid_courses += 1
        
        return int(total_fees / valid_courses) if valid_courses > 0 else 0

    def _generate_highlights(self, row) -> List[str]:
        """Generate highlights based on available college data"""
        highlights = []
        affiliation = row.get('Affiliation')
        ctype = row.get('Type')
        scholarship = row.get('Scholarship')
        website = row.get('Website')
        contact = row.get('Contact')

        if affiliation and "university" in affiliation.lower():
            highlights.append("University affiliated")

        if ctype:
            highlights.append(f"{ctype} institution")

        if scholarship and scholarship.lower() != "n/a":
            highlights.append("Scholarship available")

        if website:
            highlights.append("Online presence")

        if contact:
            highlights.append("Direct contact available")

        if not highlights:
            highlights = ["Quality education", "Good infrastructure", "Experienced faculty"]

        return highlights[:4]