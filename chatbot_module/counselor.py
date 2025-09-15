# from datetime import datetime
# from chatbot_module.models import StudentConversation, DynamicStudentProfile
# import logging
# import re
# import json
# from typing import Dict, Any, List
# from sqlalchemy import create_engine, text
# import pandas as pd
# from chatbot_module.config import DATABASE_URI

# class DynamicCollegeCounselorBot:
#     """Enhanced counselor class for FastAPI integration with PostgreSQL database"""

#     def __init__(self, api_key=None, name="Lauren"):
#         self.name = name
#         self.model = "gpt-4o"
        
#         self.engine = create_engine(DATABASE_URI)
        
#         # Initialize OpenAI client if API key is provided
#         if api_key:
#             try:
#                 from openai import OpenAI
#                 self.client = OpenAI(api_key=api_key)
#                 self.use_openai = True
#                 print("✅ OpenAI client initialized successfully")
#             except ImportError:
#                 print("⚠️  OpenAI library not installed, using mock responses")
#                 self.use_openai = False
#             except Exception as e:
#                 print(f"⚠️  OpenAI initialization failed: {e}, using mock responses")
#                 self.use_openai = False
#         else:
#             self.use_openai = False
#             print("⚠️  No API key provided, using mock responses")
        
#         # Initialize conversation tracking
#         self.conversation = StudentConversation()
#         self.student_profile = DynamicStudentProfile()
#         self.message_count = 0
#         self.sufficient_info_collected = False
#         self.extraction_history = []
#         self.conversation_stage = "greeting"
#         self.recommendations_provided = False
#         self.conversation_history = []
        
#         # Initialize career insights (keep existing)
#         self.career_insights = self._initialize_career_insights()

#     def _fetch_colleges_from_database(self) -> List[Dict]:
#         """Fetch all colleges from PostgreSQL database"""
#         try:
#             query = """
#             SELECT
#                 College_ID,
#                 College_Name,
#                 Name,
#                 Type,
#                 Affiliation,
#                 Location,
#                 Website,
#                 Contact,
#                 Email,
#                 Courses,
#                 Scholarship,
#                 Admission_Process
#             FROM college
#             """
            
#             with self.engine.connect() as conn:
#                 result = conn.execute(text(query))
#                 colleges = []
                
#                 # Fetch all rows from the result set
#                 rows = result.fetchall()
                
#                 for row in rows:
#                     # Create a dictionary from the row data for easier access
#                     column_names = [
#                         'College_ID', 'College_Name', 'Name', 'Type', 'Affiliation', 'Location',
#                         'Website', 'Contact', 'Email', 'Courses', 'Scholarship', 'Admission_Process'
#                     ]
#                     row_dict = dict(zip(column_names, row))

#                     # Parse JSON courses data
#                     courses_data = []
#                     # Check if 'Courses' key exists and its value is not None
#                     if row_dict.get('Courses'):
#                         try:
#                             # Handle both JSON string and already parsed data
#                             if isinstance(row_dict['Courses'], str):
#                                 courses_data = json.loads(row_dict['Courses'])
#                             else:
#                                 # Assume it's already a list or other iterable
#                                 courses_data = row_dict['Courses']
#                         except (json.JSONDecodeError, TypeError) as e:
#                             logging.error(f"Error decoding courses data for college {row_dict.get('College_ID')}: {e}")
#                             courses_data = []
                    
#                     # Extract course categories for streams
#                     streams = []
#                     specialties = []
#                     if courses_data:
#                         for course in courses_data:
#                             if isinstance(course, dict):
#                                 category = course.get('Category', '')
#                                 if category:  # Ensure category is not an empty string
#                                     if category not in streams:
#                                         streams.append(category)
#                                         specialties.append(category)
                    
#                     # Map database fields to expected format using the dictionary
#                     college_data = {
#                         "id": row_dict.get('College_ID'),
#                         "name": row_dict.get('College_Name') or row_dict.get('Name'),
#                         "location": row_dict.get('Location') or "Not specified",
#                         "type": row_dict.get('Type') or "General",
#                         "affiliation": row_dict.get('Affiliation') or "Not specified",
#                         "website": row_dict.get('Website'),
#                         "contact": row_dict.get('Contact'),
#                         "email": row_dict.get('Email'),
#                         "courses": courses_data,
#                         "streams": streams,
#                         "specialties": specialties,
#                         "admission": row_dict.get('Admission_Process') or "Various entrance exams",
#                         "scholarship": row_dict.get('Scholarship') or "Available",
#                         # Extract fees from courses data
#                         "fees": self._extract_fees_from_courses(courses_data),
#                         # Generate highlights based on available data
#                         "highlights": self._generate_highlights(row_dict)
#                     }
#                     colleges.append(college_data)
                
#                 return colleges
                
#         except Exception as e:
#             logging.error(f"Error fetching colleges from database: {e}")
#             return []
        
#     def _extract_fees_from_courses(self, courses_data) -> int:
#         """Extract average fees from courses data"""
#         if not courses_data:
#             return 0
        
#         total_fees = 0
#         valid_courses = 0
        
#         for course in courses_data:
#             if isinstance(course, dict) and 'Fees' in course:
#                 fees_str = str(course['Fees']).lower()
#                 # Extract numeric values from fees string
#                 import re
#                 numbers = re.findall(r'\d+', fees_str)
#                 if numbers:
#                     # Convert to integer, assume it's in appropriate units
#                     fee_amount = int(numbers[0])
#                     # If fee seems too small, multiply by 1000 (assuming it's in thousands)
#                     if fee_amount < 1000:
#                         fee_amount *= 1000
#                     total_fees += fee_amount
#                     valid_courses += 1
        
#         return int(total_fees / valid_courses) if valid_courses > 0 else 0

#     def _generate_highlights(self, row) -> List[str]:
#         """Generate highlights based on available college data"""
#         highlights = []

#         # use dict.get() instead of attribute access
#         affiliation = row.get('Affiliation')
#         ctype = row.get('Type')
#         scholarship = row.get('Scholarship')
#         website = row.get('Website')
#         contact = row.get('Contact')

#         if affiliation and "university" in affiliation.lower():
#             highlights.append("University affiliated")

#         if ctype:
#             highlights.append(f"{ctype} institution")

#         if scholarship and scholarship.lower() != "n/a":
#             highlights.append("Scholarship available")

#         if website:
#             highlights.append("Online presence")

#         if contact:
#             highlights.append("Direct contact available")

#         if not highlights:
#             highlights = ["Quality education", "Good infrastructure", "Experienced faculty"]

#         return highlights[:4]

#     def _search_colleges_by_criteria(self, field_keywords=None, location=None, college_type=None) -> List[Dict]:
#         """Search colleges based on specific criteria"""
#         try:
#             query = "SELECT * FROM college WHERE 1=1"
#             params = {}
#             logging.info(f"Location: {location}, College Type: {college_type}, Field Keywords: {field_keywords}")
            
#             if field_keywords:
#                 # Search in courses JSON and college type
#                 query += " AND (LOWER(courses::text) LIKE :field_keyword OR LOWER(type) LIKE :field_keyword)"
#                 # Use first keyword for search
#                 keyword = field_keywords[0].lower()
#                 params['field_keyword'] = f'%{keyword}%'
            
#             if location:
#                 query += " AND LOWER(location) LIKE :location"
#                 params['location'] = f'%{location.lower()}%'
            
#             if college_type:
#                 query += " AND LOWER(type) LIKE :college_type"
#                 params['college_type'] = f'%{college_type.lower()}%'
            
#             with self.engine.connect() as conn:
#                 result = conn.execute(text(query), params)
#                 colleges = []
                
#                 for row in result:
#                     # Parse and format similar to _fetch_colleges_from_database
#                     courses_data = []
#                     if row.Courses:
#                         try:
#                             courses_data = json.loads(row.Courses) if isinstance(row.Courses, str) else row.Courses
#                         except (json.JSONDecodeError, TypeError):
#                             courses_data = []
                    
#                     streams = []
#                     if courses_data:
#                         for course in courses_data:
#                             if isinstance(course, dict):
#                                 category = course.get('Category', '')
#                                 if category and category not in streams:
#                                     streams.append(category)
                    
#                     college_data = {
#                         "id": row.College_ID,
#                         "name": row.College_Name or row.Name,
#                         "location": row.Location or "Not specified",
#                         "type": row.Type or "General",
#                         "affiliation": row.Affiliation or "Not specified",
#                         "website": row.Website,
#                         "contact": row.Contact,
#                         "email": row.Email,
#                         "courses": courses_data,
#                         "streams": streams,
#                         "specialties": streams,
#                         "admission": row.Admission_Process or "Various entrance exams",
#                         "scholarship": row.Scholarship or "Available",
#                         "fees": self._extract_fees_from_courses(courses_data),
#                         "highlights": self._generate_highlights(row)
#                     }
#                     colleges.append(college_data)
                
#                 return colleges
                
#         except Exception as e:
#             logging.error(f"Error searching colleges: {e}")
#             return []

#     def _initialize_career_insights(self):
#         """Initialize career insights database"""
#         return {
#             "high_growth_careers": {
#                 "technology": {
#                     "Software Engineer": {
#                         "description": "Design and develop software applications",
#                         "skills_required": ["Programming", "Problem-solving", "System design"],
#                         "education_path": ["B.Tech Computer Science", "BCA + MCA", "Self-learning + certifications"],
#                         "salary_range": "₹4-50 lakhs per year",
#                         "growth_prospects": "Excellent - High demand, startup opportunities, global market"
#                     },
#                     "Data Scientist": {
#                         "description": "Analyze complex data to derive business insights",
#                         "skills_required": ["Statistics", "Machine Learning", "Python/R", "SQL"],
#                         "education_path": ["B.Tech + Data Science certification", "Statistics/Math degree + upskilling"],
#                         "salary_range": "₹6-40 lakhs per year",
#                         "growth_prospects": "Very High - Every industry needs data insights"
#                     }
#                 },
#                 "healthcare": {
#                     "Doctor": {
#                         "description": "Diagnose and treat medical conditions",
#                         "skills_required": ["Medical knowledge", "Empathy", "Decision-making", "Communication"],
#                         "education_path": ["MBBS + MD/MS specialization"],
#                         "salary_range": "₹6-50+ lakhs per year",
#                         "growth_prospects": "Stable - Always in demand"
#                     }
#                 },
#                 "business": {
#                     "Management Consultant": {
#                         "description": "Help organizations solve complex business problems",
#                         "skills_required": ["Analytical thinking", "Communication", "Industry knowledge"],
#                         "education_path": ["Any graduation + MBA from top school"],
#                         "salary_range": "₹8-40 lakhs per year",
#                         "growth_prospects": "Excellent - High learning curve, global opportunities"
#                     }
#                 }
#             }
#         }

#     def _analyze_conversation_context(self, user_message: str) -> Dict[str, Any]:
#         """Analyze conversation context to determine if recommendations are appropriate"""
#         message_lower = user_message.lower()
#         context_analysis = {
#             "should_recommend": False,
#             "recommendation_type": None,
#             "confidence": 0.0
#         }
        
#         # Direct requests for recommendations
#         direct_triggers = ["recommend", "suggest", "college", "university", "institute"]
#         if any(trigger in message_lower for trigger in direct_triggers):
#             context_analysis["should_recommend"] = True
#             context_analysis["confidence"] = 0.9
#             context_analysis["recommendation_type"] = "direct_request"
#             return context_analysis
        
#         # Contextual triggers based on conversation stage
#         if self.conversation_stage in ["recommendation", "detailed_guidance"]:
#             # Questions about options/choices
#             option_questions = ["what should i", "which one", "options", "choices", "what are"]
#             if any(question in message_lower for question in option_questions):
#                 context_analysis["should_recommend"] = True
#                 context_analysis["confidence"] = 0.8
#                 context_analysis["recommendation_type"] = "option_inquiry"
#                 return context_analysis
        
#         # Academic/career discussions with sufficient profile info
#         academic_keywords = ["study", "course", "degree", "program", "career", "future"]
#         if any(keyword in message_lower for keyword in academic_keywords):
#             if self.sufficient_info_collected:
#                 context_analysis["should_recommend"] = True
#                 context_analysis["confidence"] = 0.7
#                 context_analysis["recommendation_type"] = "academic_discussion"
#                 return context_analysis
        
#         # User expressing confusion or need for guidance
#         confusion_phrases = ["confused", "don't know", "unsure", "help me", "need guidance"]
#         if any(phrase in message_lower for phrase in confusion_phrases):
#             if self.message_count > 3:  # After some conversation
#                 context_analysis["should_recommend"] = True
#                 context_analysis["confidence"] = 0.6
#                 context_analysis["recommendation_type"] = "guidance_needed"
#                 return context_analysis
        
#         return context_analysis

#     def _get_dynamic_system_prompt(self):
#         """Generate dynamic system prompt based on conversation stage"""
#         base_personality = f"""
#         You are {self.name}, an expert AI college counselor with deep knowledge of Indian and global education systems. 
#         You have years of experience helping students navigate their educational journey.

#         Your Core Qualities:
#         - Warm, encouraging, and genuinely interested in each student's success
#         - Highly knowledgeable about colleges, careers, and education trends
#         - Patient listener who asks thoughtful follow-up questions
#         - Provides specific, actionable advice rather than generic responses
#         - Shares relevant insights and stories to help students understand options
#         - Balances dreams with practical realities
#         - Proactively provides college recommendations when appropriate based on context

#         Current conversation stage: {self.conversation_stage}
#         Messages exchanged: {self.message_count}
#         Sufficient info collected: {self.sufficient_info_collected}
        
#         Based on the conversation, provide helpful, informative responses that guide the student toward making informed decisions about their education and career.
        
#         When appropriate (based on conversation context and available student information), 
#         proactively provide college recommendations without waiting for explicit requests.
#         """
        
#         return base_personality

#     def _update_conversation_stage(self, user_message):
#         """Update conversation stage based on content and message count"""
#         message_lower = user_message.lower()
        
#         if self.message_count <= 2:
#             self.conversation_stage = "greeting"
#         elif self.message_count <= 5:
#             self.conversation_stage = "information_gathering"
#         elif any(word in message_lower for word in ["recommend", "suggest", "what should i", "help me choose"]):
#             self.conversation_stage = "recommendation"
#         elif self.message_count > 5:
#             self.conversation_stage = "detailed_guidance"

#     def _extract_student_information(self, user_message: str) -> Dict[str, Any]:
#         """Extract and update student information from conversation"""
#         message_lower = user_message.lower()
#         updates: Dict[str, Any] = {}

#         # === Name (very basic placeholder detection, refine with NLP later) ===
#         if "my name is" in message_lower:
#             name = user_message.split("my name is")[-1].strip().split(" ")[0].title()
#             self.student_profile.name = name
#             updates["name"] = name

#         # === Age ===
#         age_match = re.search(r"\b(\d{2})\s*years?\s*old\b", message_lower)
#         if age_match:
#             age = int(age_match.group(1))
#             self.student_profile.age = age
#             updates["age"] = age

#         # === Academic Performance / Scores ===
#         marks_match = re.search(r"(\d{1,3})\s*%|percent", message_lower)
#         if marks_match:
#             percent = float(marks_match.group(1))
#             self.student_profile.academic_performance["overall"] = percent
#             self.student_profile.scores["percentage"] = percent
#             updates["academic_performance"] = {"overall": percent}

#         percentile_match = re.search(r"(\d{1,3})\s*percentile", message_lower)
#         if percentile_match:
#             perc = float(percentile_match.group(1))
#             self.student_profile.scores["percentile"] = perc
#             updates["scores"] = {"percentile": perc}

#         # === Interests / Preferred Fields ===
#         tech_keywords = ["computer", "programming", "software", "coding", "tech", "it"]
#         if any(word in message_lower for word in tech_keywords):
#             if "Computer Science" not in self.student_profile.preferred_fields:
#                 self.student_profile.preferred_fields.append("Computer Science")
#                 self.student_profile.interests.append("Technology")
#                 updates["preferred_fields"] = self.student_profile.preferred_fields

#         medical_keywords = ["doctor", "medical", "medicine", "healthcare", "mbbs"]
#         if any(word in message_lower for word in medical_keywords):
#             if "Medicine" not in self.student_profile.preferred_fields:
#                 self.student_profile.preferred_fields.append("Medicine")
#                 self.student_profile.interests.append("Healthcare")
#                 updates["preferred_fields"] = self.student_profile.preferred_fields

#         business_keywords = ["business", "management", "mba", "finance", "marketing"]
#         if any(word in message_lower for word in business_keywords):
#             if "Business" not in self.student_profile.preferred_fields:
#                 self.student_profile.preferred_fields.append("Business")
#                 self.student_profile.interests.append("Business")
#                 updates["preferred_fields"] = self.student_profile.preferred_fields

#         # === Location Preference ===
#         for city in ["delhi", "mumbai", "bangalore", "pune", "hyderabad", "chennai", "kolkata", "indore"]:
#             if city in message_lower:
#                 self.student_profile.location_preference = city.title()
#                 updates["location_preference"] = city.title()

#         # === Budget (₹ or lakh keywords) ===
#         budget_match = re.search(r"(\d+(\.\d+)?)\s*(lakh|lakhs|₹)", message_lower)
#         if budget_match:
#             amount = float(budget_match.group(1))
#             if "lakh" in budget_match.group(3):
#                 amount *= 100000
#             self.student_profile.budget = int(amount)
#             updates["budget"] = int(amount)

#         # === Career Goals ===
#         if "research" in message_lower:
#             self.student_profile.career_goals.append("Research")
#         if "entrepreneur" in message_lower or "startup" in message_lower:
#             self.student_profile.career_goals.append("Entrepreneurship")
#         if "abroad" in message_lower:
#             self.student_profile.career_goals.append("Study Abroad")
#         if self.student_profile.career_goals:
#             updates["career_goals"] = self.student_profile.career_goals

#         # === Extracurricular Activities ===
#         if "sports" in message_lower:
#             self.student_profile.extracurricular.append("Sports")
#         if "music" in message_lower:
#             self.student_profile.extracurricular.append("Music")
#         if "arts" in message_lower or "drawing" in message_lower:
#             self.student_profile.extracurricular.append("Arts")
#         if self.student_profile.extracurricular:
#             updates["extracurricular"] = self.student_profile.extracurricular

#         # === Exams (academic context) ===
#         if "jee" in message_lower:
#             self.student_profile.additional_info["exam"] = "JEE"
#         if "neet" in message_lower:
#             self.student_profile.additional_info["exam"] = "NEET"
#         if "cat" in message_lower:
#             self.student_profile.additional_info["exam"] = "CAT"

#         # === Family Background (basic detection) ===
#         if "first generation" in message_lower:
#             self.student_profile.family_background["education"] = "First Generation Learner"
#         if "parents are doctors" in message_lower:
#             self.student_profile.family_background["profession"] = "Medical"
#         if self.student_profile.family_background:
#             updates["family_background"] = self.student_profile.family_background

#         # === Mark info collected (removed budget dependency) ===
#         if self.student_profile.preferred_fields and self.student_profile.scores:
#             self.sufficient_info_collected = True
        
#         return updates

#     def chat(self, message, context):
#         """Main chat function with OpenAI integration"""
#         self.message_count += 1
        
#         # Update conversation stage and extract information
#         self._update_conversation_stage(message)
#         self._extract_student_information(message)
        
#         # Analyze conversation context for recommendations
#         context_analysis = self._analyze_conversation_context(message)
        
#         # Add to extraction history
#         self.extraction_history.append({
#             "message": message,
#             "stage": self.conversation_stage,
#             "context_analysis": context_analysis,
#             "timestamp": datetime.now().isoformat()
#         })
        
#         # Add to conversation history
#         self.conversation_history.append({
#             "role": "user",
#             "content": message,
#             "timestamp": datetime.now().isoformat()
#         })
        
#         if self.use_openai:
#             try:
#                 # Prepare messages for OpenAI
#                 system_prompt = self._get_dynamic_system_prompt()
                
#                 messages = [
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": message}
#                 ]
                
#                 # Add recent conversation context (last 4 exchanges)
#                 recent_history = self.conversation_history[-8:]  # Last 4 exchanges (user + assistant)
#                 for i in range(0, len(recent_history)-1, 2):  # Skip current message
#                     if i+1 < len(recent_history):
#                         messages.insert(-1, {"role": "user", "content": recent_history[i]["content"]})
#                         messages.insert(-1, {"role": "assistant", "content": recent_history[i+1]["content"]})
                
#                 response = self.client.chat.completions.create(
#                     model=self.model,
#                     messages=messages,
#                     temperature=0.7,
#                     max_tokens=1000,
#                     frequency_penalty=0.3,
#                     presence_penalty=0.2
#                 )
                
#                 assistant_response = response.choices[0].message.content
                
#             except Exception as e:
#                 print(f"OpenAI API error: {e}")
#                 assistant_response = self._get_fallback_response(message)
#         else:
#             assistant_response = self._get_fallback_response(message)
        
#         # Add assistant response to history
#         self.conversation_history.append({
#             "role": "assistant",
#             "content": assistant_response,
#             "timestamp": datetime.now().isoformat()
#         })
        
#         return assistant_response

#     def _get_fallback_response(self, message):
#         """Provide intelligent fallback responses when OpenAI is not available"""
#         message_lower = message.lower()
        
#         if self.message_count == 1:
#             return f"Hello! I'm {self.name}, your AI college counselor. I'm here to help you navigate your educational journey and find the best college options for your goals. Could you tell me a bit about yourself - what are you currently studying and what fields interest you most?"
        
#         # Handle specific queries
#         if any(word in message_lower for word in ["engineering", "iit", "jee", "computer science"]):
#             return """Great choice! Engineering offers excellent career prospects. Some top options include:

# 🏆 **IITs** - Premier institutes with world-class education (Admission: JEE Advanced)
# 🎯 **NITs** - Excellent government institutes across India (Admission: JEE Main)  
# ⭐ **BITS Pilani** - Top private institute with industry focus (Admission: BITSAT)
# 🏫 **State colleges** - Good quality education at affordable fees

# Computer Science is particularly hot right now with amazing placement opportunities. What's your current academic background? Are you preparing for JEE or any other entrance exams?"""

#         elif any(word in message_lower for word in ["medical", "doctor", "neet", "mbbs"]):
#             return """Medicine is a noble and rewarding career path! Here's what you should know:

# 🏥 **AIIMS** - Premier medical institutes with highly subsidized fees
# 🎓 **Government Medical Colleges** - Affordable with excellent clinical exposure
# 🏫 **Private Medical Colleges** - Good infrastructure but higher fees (₹50L - ₹1.5Cr)

# Key points:
# - NEET is mandatory for all medical admissions
# - Start preparation early - very competitive field
# - Consider specialization options after MBBS
# - Alternative paths: BDS, AYUSH, Allied Health Sciences

# What's your current academic performance? Have you started NEET preparation?"""

#         elif any(word in message_lower for word in ["mba", "management", "business", "cat"]):
#             return """Business education opens doors to diverse career opportunities!

# 🎯 **IIMs** - Top business schools with excellent ROI (Admission: CAT)
# ⭐ **ISB, XLRI, FMS** - Premier institutes with strong placements  
# 📈 **Sectoral MBAs** - Healthcare, Rural, Family Business specializations

# Career paths:
# - Management Consulting (₹15-40L starting)
# - Investment Banking & Finance  
# - Product Management in Tech
# - General Management roles

# Most MBA programs prefer 2-3 years work experience. Are you currently working or planning to work before MBA? What business areas interest you most?"""

#         elif any(word in message_lower for word in ["confused", "help", "don't know", "unsure"]):
#             return """It's completely normal to feel confused about career choices! Let's explore your options systematically.

# Let me ask you a few questions to better understand your interests:

# 🤔 **Academic Performance**: How are your current grades? Which subjects do you enjoy most?
# 🎯 **Interests**: What activities make you lose track of time? 
# 💡 **Career Vision**: Where do you see yourself in 10 years?
# 💰 **Practical Considerations**: Any budget constraints or location preferences?
# 👨‍👩‍👧‍👦 **Family Input**: What does your family suggest?

# Based on your responses, I can provide personalized recommendations. What would you like to share first?"""

#         else:
#             return """Thank you for sharing that! I'm learning about your preferences and goals.

# Based on our conversation so far, I can see you're exploring your options thoughtfully. Here are some areas we could discuss further:

# 📚 **Academic Paths**: Engineering, Medical, Business, Liberal Arts, Sciences
# 🌎 **Study Locations**: India vs International options  
# 💼 **Career Prospects**: Emerging fields vs Traditional stable careers
# 💰 **Financial Planning**: Education costs, scholarships, loans

# What specific aspect would you like to dive deeper into? I'm here to provide detailed insights to help you make informed decisions!"""

#     def generate_personalized_recommendations(self, profile=None):
#         """Generate recommendations based on student profile using database"""
#         recommendations = []
        
#         # Use persisted DB profile if provided
#         if not profile:
#             profile = self.student_profile

#         preferred_fields = getattr(profile, "preferred_fields", []) or []
#         location_preference = getattr(profile, "location_preference", None)

#         # Fetch colleges from database based on preferences
#         if preferred_fields:
#             # Search for colleges that match preferred fields
#             all_colleges = self._search_colleges_by_criteria(
#                 field_keywords=preferred_fields,
#                 location=location_preference
#             )
#         else:
#             # Get all colleges if no specific field preference
#             all_colleges = self._fetch_colleges_from_database()

#         # Filter and score colleges based on student preferences
#         for college in all_colleges:
#             score = 0
#             reasons = []
            
#             # Check field alignment
#             if preferred_fields:
#                 college_streams = college.get('streams', [])
#                 college_courses = college.get('courses', [])
                
#                 field_match = False
#                 # Check streams
#                 if college_streams:
#                     field_match = any(
#                         any(pref.lower() in stream.lower() for stream in college_streams)
#                         for pref in preferred_fields
#                     )
                
#                 # Also check in courses data
#                 if not field_match and college_courses:
#                     for course in college_courses:
#                         if isinstance(course, dict):
#                             course_category = course.get('Category', '').lower()
#                             if any(pref.lower() in course_category for pref in preferred_fields):
#                                 field_match = True
#                                 break
                
#                 if field_match:
#                     score += 50
#                     reasons.append(f"Offers programs in {', '.join(preferred_fields)}")
            
#             # Location preference
#             if location_preference:
#                 if location_preference.lower() in college.get('location', '').lower():
#                     score += 25
#                     reasons.append("Preferred location")
            
#             # Quality indicators
#             if college.get('affiliation'):
#                 score += 10
                
#             if college.get('scholarship') and college.get('scholarship').lower() != "n/a":
#                 score += 15
#                 reasons.append("Scholarships available")
                
#             if college.get('website'):
#                 score += 5
                
#             # Add base score for having complete information
#             score += len(college.get('highlights', [])) * 3
            
#             if score > 15:  # Minimum threshold
#                 recommendations.append({
#                     "name": college['name'],
#                     "location": college['location'],
#                     "fees": college.get('fees', 0),
#                     "match_score": min(score, 100.0),
#                     "match_reasons": reasons or ["Good overall fit based on your profile"],
#                     "type": college.get('type', 'General'),
#                     "admission": college.get('admission', 'Various entrance exams'),
#                     "highlights": college.get('highlights', [])[:3],
#                     "website": college.get('website'),
#                     "contact": college.get('contact'),
#                     "email": college.get('email'),
#                     "scholarship": college.get('scholarship'),
#                     "affiliation": college.get('affiliation')
#                 })
        
#         # Sort by match score and return top recommendations
#         recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
#         return recommendations[:10] if recommendations else []

from datetime import datetime
from chatbot_module.models import StudentConversation, DynamicStudentProfile
import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import create_engine, text
import pandas as pd
from chatbot_module.config import DATABASE_URI

class DynamicCollegeCounselorBot:
    """Enhanced counselor class with improved recommendation system"""

    def __init__(self, api_key=None, name="Lauren"):
        self.name = name
        self.model = "gpt-4o"
        
        self.engine = create_engine(DATABASE_URI)
        
        # Initialize OpenAI client if API key is provided
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.use_openai = True
                print("✅ OpenAI client initialized successfully")
            except ImportError:
                print("⚠️  OpenAI library not installed, using mock responses")
                self.use_openai = False
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}, using mock responses")
                self.use_openai = False
        else:
            self.use_openai = False
            print("⚠️  No API key provided, using mock responses")
        
        # Initialize conversation tracking
        self.conversation = StudentConversation()
        self.student_profile = DynamicStudentProfile()
        self.message_count = 0
        self.sufficient_info_collected = False
        self.extraction_history = []
        self.conversation_stage = "greeting"
        self.recommendations_provided = False
        self.conversation_history = []
        
        # Initialize career insights
        self.career_insights = self._initialize_career_insights()
        
        # Cache for colleges data to reduce database queries
        self.colleges_cache = None
        self.cache_timestamp = None

    def _get_colleges_data(self, force_refresh=False) -> List[Dict]:
        """Get colleges data with caching mechanism"""
        current_time = datetime.now()
        
        # Refresh cache if forced or if cache is older than 1 hour
        if (force_refresh or self.colleges_cache is None or 
            self.cache_timestamp is None or 
            (current_time - self.cache_timestamp).total_seconds() > 3600):
            
            self.colleges_cache = self._fetch_colleges_from_database()
            self.cache_timestamp = current_time
            
        return self.colleges_cache

    def _fetch_colleges_from_database(self) -> List[Dict]:
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
                
                # Fetch all rows from the result set
                rows = result.fetchall()
                
                for row in rows:
                    # Create a dictionary from the row data for easier access
                    column_names = [
                        'College_ID', 'College_Name', 'Name', 'Type', 'Affiliation', 'Location',
                        'Website', 'Contact', 'Email', 'Courses', 'Scholarship', 'Admission_Process'
                    ]
                    row_dict = dict(zip(column_names, row))

                    # Parse JSON courses data
                    courses_data = []
                    # Check if 'Courses' key exists and its value is not None
                    if row_dict.get('Courses'):
                        try:
                            # Handle both JSON string and already parsed data
                            if isinstance(row_dict['Courses'], str):
                                courses_data = json.loads(row_dict['Courses'])
                            else:
                                # Assume it's already a list or other iterable
                                courses_data = row_dict['Courses']
                        except (json.JSONDecodeError, TypeError) as e:
                            logging.error(f"Error decoding courses data for college {row_dict.get('College_ID')}: {e}")
                            courses_data = []
                    
                    # Extract course categories for streams
                    streams = []
                    specialties = []
                    if courses_data:
                        for course in courses_data:
                            if isinstance(course, dict):
                                category = course.get('Category', '')
                                if category:  # Ensure category is not an empty string
                                    if category not in streams:
                                        streams.append(category)
                                        specialties.append(category)
                    
                    # Map database fields to expected format using the dictionary
                    college_data = {
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
                        # Extract fees from courses data
                        "fees": self._extract_fees_from_courses(courses_data),
                        # Generate highlights based on available data
                        "highlights": self._generate_highlights(row_dict)
                    }
                    colleges.append(college_data)
                
                return colleges
                
        except Exception as e:
            logging.error(f"Error fetching colleges from database: {e}")
            return []

    def _extract_fees_from_courses(self, courses_data) -> int:
        """Extract average fees from courses data"""
        if not courses_data:
            return 0
        
        total_fees = 0
        valid_courses = 0
        
        for course in courses_data:
            if isinstance(course, dict) and 'Fees' in course:
                fees_str = str(course['Fees']).lower()
                # Extract numeric values from fees string
                import re
                numbers = re.findall(r'\d+', fees_str)
                if numbers:
                    # Convert to integer, assume it's in appropriate units
                    fee_amount = int(numbers[0])
                    # If fee seems too small, multiply by 1000 (assuming it's in thousands)
                    if fee_amount < 1000:
                        fee_amount *= 1000
                    total_fees += fee_amount
                    valid_courses += 1
        
        return int(total_fees / valid_courses) if valid_courses > 0 else 0

    def _generate_highlights(self, row) -> List[str]:
        """Generate highlights based on available college data"""
        highlights = []

        # use dict.get() instead of attribute access
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

    def _search_colleges_by_criteria(self, field_keywords=None, location=None, college_type=None, 
                                   budget_range=None, exam_preference=None) -> List[Dict]:
        """Enhanced search for colleges based on multiple criteria"""
        try:
            # Get all colleges first (using cache)
            all_colleges = self._get_colleges_data()
            
            # Filter colleges based on criteria
            filtered_colleges = []
            
            for college in all_colleges:
                match_score = 0
                
                # Field/keyword matching
                if field_keywords:
                    field_match = False
                    college_streams = college.get('streams', [])
                    college_courses = college.get('courses', [])
                    
                    # Check if any field keyword matches college streams
                    for keyword in field_keywords:
                        keyword_lower = keyword.lower()
                        
                        # Check in streams
                        for stream in college_streams:
                            if keyword_lower in stream.lower():
                                field_match = True
                                match_score += 30
                                break
                        
                        # Check in course names if not found in streams
                        if not field_match and college_courses:
                            for course in college_courses:
                                if isinstance(course, dict):
                                    course_name = course.get('Course_Name', '').lower()
                                    if keyword_lower in course_name:
                                        field_match = True
                                        match_score += 25
                                        break
                    
                    # If no field match and we have field criteria, skip this college
                    if not field_match and field_keywords:
                        continue
                
                # Location matching
                if location:
                    location_lower = location.lower()
                    college_location = college.get('location', '').lower()
                    
                    if location_lower in college_location:
                        match_score += 20
                    else:
                        # If location is specified but doesn't match, reduce score but don't exclude
                        match_score -= 10
                
                # College type matching
                if college_type:
                    college_type_lower = college_type.lower()
                    actual_type = college.get('type', '').lower()
                    
                    if college_type_lower in actual_type:
                        match_score += 15
                
                # Budget consideration
                if budget_range and college.get('fees', 0) > 0:
                    college_fees = college.get('fees', 0)
                    min_budget, max_budget = budget_range
                    
                    if min_budget <= college_fees <= max_budget:
                        match_score += 20
                    elif college_fees < min_budget:
                        match_score += 10  # Cheaper is generally good
                    else:
                        match_score -= 15  # Too expensive
                
                # Add college with match score
                if match_score >= 0:  # Only include colleges with non-negative scores
                    college_with_score = college.copy()
                    college_with_score['match_score'] = match_score
                    filtered_colleges.append(college_with_score)
            
            # Sort by match score (highest first)
            filtered_colleges.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            return filtered_colleges
            
        except Exception as e:
            logging.error(f"Error searching colleges: {e}")
            return []

    def _extract_preferences_from_conversation(self) -> Dict[str, Any]:
        """Extract preferences from the entire conversation history"""
        preferences = {
            "fields": set(),
            "location": None,
            "college_type": None,
            "budget_range": (0, float('inf')),
            "exam_preference": None
        }
        
        # Analyze conversation history for preferences
        for message in self.conversation_history:
            if message["role"] == "user":
                content = message["content"].lower()
                
                # Field preferences
                field_keywords = {
                    "engineering": ["engineering", "engineer", "technical", "technology", "tech"],
                    "medical": ["medical", "medicine", "doctor", "mbbs", "neet"],
                    "business": ["business", "management", "mba", "commerce", "marketing"],
                    "arts": ["arts", "humanities", "literature", "history", "philosophy"],
                    "science": ["science", "physics", "chemistry", "biology", "math"]
                }
                
                for field, keywords in field_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        preferences["fields"].add(field)
                
                # Location preference
                locations = ["delhi", "mumbai", "bangalore", "chennai", "kolkata", "hyderabad", 
                           "pune", "ahmedabad", "jaipur", "indore", "bhopal"]
                for location in locations:
                    if location in content:
                        preferences["location"] = location.title()
                        break
                
                # College type preference
                college_types = {
                    "government": ["government", "govt", "public"],
                    "private": ["private", "self-financed"],
                    "deemed": ["deemed", "deemed university"],
                    "iit": ["iit", "indian institute of technology"],
                    "nit": ["nit", "national institute of technology"],
                    "iim": ["iim", "indian institute of management"]
                }
                
                for college_type, keywords in college_types.items():
                    if any(keyword in content for keyword in keywords):
                        preferences["college_type"] = college_type
                        break
                
                # Budget preference
                budget_patterns = [
                    r"budget.*?(\d+)\s*(\w+)\s*to\s*(\d+)\s*(\w+)",
                    r"(\d+)\s*to\s*(\d+)\s*(lakh|lakhs|lac|lacs)",
                    r"around\s*(\d+)\s*(lakh|lakhs|lac|lacs)",
                    r"upto\s*(\d+)\s*(lakh|lakhs|lac|lacs)",
                    r"max.*?(\d+)\s*(lakh|lakhs|lac|lacs)"
                ]
                
                for pattern in budget_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        if len(matches[0]) == 4:  # Range like "5 to 10 lakhs"
                            min_val = int(matches[0][0])
                            max_val = int(matches[0][2])
                            unit = matches[0][3].lower()
                        else:  # Single value like "around 5 lakhs"
                            min_val = 0
                            max_val = int(matches[0][0])
                            unit = matches[0][1].lower()
                        
                        # Convert to rupees
                        if 'lakh' in unit or 'lac' in unit:
                            min_val *= 100000
                            max_val *= 100000
                        
                        preferences["budget_range"] = (min_val, max_val)
                        break
                
                # Exam preference
                exams = {
                    "jee": ["jee", "joint entrance"],
                    "neet": ["neet", "national eligibility"],
                    "cat": ["cat", "common admission"],
                    "upsc": ["upsc", "civil services"],
                    "gate": ["gate", "graduate aptitude"]
                }
                
                for exam, keywords in exams.items():
                    if any(keyword in content for keyword in keywords):
                        preferences["exam_preference"] = exam
                        break
        
        # Convert set to list
        preferences["fields"] = list(preferences["fields"])
        
        return preferences

    def _get_recommendations_based_on_context(self) -> Tuple[List[Dict], bool]:
        """
        Get college recommendations based on conversation context
        Returns: (recommendations, found_in_database)
        """
        # Extract preferences from conversation
        preferences = self._extract_preferences_from_conversation()
        
        # If no specific fields mentioned but we have location, search by location
        if not preferences["fields"] and preferences["location"]:
            logging.info(f"Searching colleges by location: {preferences['location']}")
            colleges = self._search_colleges_by_criteria(
                location=preferences["location"],
                college_type=preferences["college_type"],
                budget_range=preferences["budget_range"]
            )
            return (colleges[:8], True)  # Return top 8 matches
        
        # If we have field preferences, search by fields
        elif preferences["fields"]:
            logging.info(f"Searching colleges by fields: {preferences['fields']}")
            colleges = self._search_colleges_by_criteria(
                field_keywords=preferences["fields"],
                location=preferences["location"],
                college_type=preferences["college_type"],
                budget_range=preferences["budget_range"],
                exam_preference=preferences["exam_preference"]
            )
            return (colleges[:10], True)  # Return top 10 matches
        
        # If we have no specific preferences, return some general recommendations
        else:
            logging.info("No specific preferences found, returning general recommendations")
            all_colleges = self._get_colleges_data()
            
            # Return a mix of different types of colleges
            diverse_colleges = []
            types_seen = set()
            
            for college in all_colleges:
                college_type = college.get('type', '').lower()
                if college_type not in types_seen:
                    diverse_colleges.append(college)
                    types_seen.add(college_type)
                
                if len(diverse_colleges) >= 6:  # Return 6 diverse colleges
                    break
            
            return (diverse_colleges, True)

    def _format_college_recommendations(self, colleges: List[Dict]) -> str:
        """Format college recommendations into a readable response"""
        if not colleges:
            return "I couldn't find any colleges matching your preferences in our database. Let me provide some general guidance instead."
        
        response = "Based on our conversation, here are some colleges that might interest you:\n\n"
        
        for i, college in enumerate(colleges[:5], 1):  # Show top 5
            response += f"**{i}. {college.get('name', 'Unknown College')}**\n"
            response += f"   📍 {college.get('location', 'Location not specified')}\n"
            response += f"   🏫 Type: {college.get('type', 'Not specified')}\n"
            
            # Show relevant streams if available
            streams = college.get('streams', [])
            if streams:
                response += f"   📚 Offers: {', '.join(streams[:3])}"
                if len(streams) > 3:
                    response += f" and {len(streams)-3} more"
                response += "\n"
            
            # Show fees if available
            fees = college.get('fees', 0)
            if fees > 0:
                response += f"   💰 Approx. fees: ₹{fees:,} per year\n"
            
            # Show admission process if available
            admission = college.get('admission', '')
            if admission and admission != "Various entrance exams":
                response += f"   🎓 Admission: {admission}\n"
            
            # Add a separator
            if i < len(colleges[:5]):
                response += "\n"
        
        response += "\nWould you like more information about any of these colleges, or would you like me to suggest options based on different criteria?"
        
        return response

    def _get_llm_fallback_recommendations(self, preferences: Dict[str, Any]) -> str:
        """Get recommendations from LLM when database doesn't have matching colleges"""
        # Build prompt for LLM based on preferences
        prompt = f"As an expert college counselor, provide recommendations for a student interested in: "
        
        if preferences["fields"]:
            prompt += f"fields: {', '.join(preferences['fields'])}. "
        
        if preferences["location"]:
            prompt += f"preferred location: {preferences['location']}. "
        
        if preferences["college_type"]:
            prompt += f"preferred college type: {preferences['college_type']}. "
        
        if preferences["budget_range"][1] < float('inf'):
            max_budget_lakhs = preferences["budget_range"][1] / 100000
            prompt += f"budget: up to {max_budget_lakhs} lakhs. "
        
        if preferences["exam_preference"]:
            prompt += f"exam preference: {preferences['exam_preference']}. "
        
        prompt += "Please suggest some colleges and provide brief details about each."
        
        if self.use_openai:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                logging.error(f"OpenAI API error in fallback: {e}")
                return self._get_general_advice_fallback()
        else:
            return self._get_general_advice_fallback()
    
    def _get_general_advice_fallback(self) -> str:
        """Provide general advice when no specific recommendations can be made"""
        return """I don't have specific college recommendations based on our conversation yet. Here's some general advice:

1. **Research thoroughly**: Look into colleges that offer programs aligned with your interests
2. **Consider multiple factors**: Look beyond rankings - consider location, campus culture, placement records, and faculty
3. **Check accreditation**: Ensure the college is recognized by appropriate bodies like UGC, AICTE, MCI, etc.
4. **Visit campuses**: If possible, visit shortlisted colleges to get a feel for the environment
5. **Talk to current students**: They can provide insights about the actual experience

Could you tell me more about your specific interests or preferences? This will help me provide more targeted recommendations."""

    def provide_recommendations(self) -> str:
        """
        Main method to provide recommendations based on conversation context
        Returns formatted recommendations
        """
        # Get recommendations from database based on context
        colleges, found_in_database = self._get_recommendations_based_on_context()
        
        if found_in_database and colleges:
            return self._format_college_recommendations(colleges)
        else:
            # Fallback to LLM if no colleges found in database
            preferences = self._extract_preferences_from_conversation()
            return self._get_llm_fallback_recommendations(preferences)

    def _analyze_conversation_context(self, user_message: str) -> Dict[str, Any]:
        """Analyze conversation context to determine if recommendations are appropriate"""
        message_lower = user_message.lower()
        context_analysis = {
            "should_recommend": False,
            "recommendation_type": None,
            "confidence": 0.0
        }
        
        # Direct requests for recommendations
        direct_triggers = ["recommend", "suggest", "college", "university", "institute", "options", "choices"]
        if any(trigger in message_lower for trigger in direct_triggers):
            context_analysis["should_recommend"] = True
            context_analysis["confidence"] = 0.9
            context_analysis["recommendation_type"] = "direct_request"
            return context_analysis
        
        # Contextual triggers based on conversation stage
        if self.conversation_stage in ["recommendation", "detailed_guidance"]:
            # Questions about options/choices
            option_questions = ["what should i", "which one", "what are", "how about", "what do you think"]
            if any(question in message_lower for question in option_questions):
                context_analysis["should_recommend"] = True
                context_analysis["confidence"] = 0.8
                context_analysis["recommendation_type"] = "option_inquiry"
                return context_analysis
        
        # Academic/career discussions with sufficient profile info
        academic_keywords = ["study", "course", "degree", "program", "career", "future", "field", "stream"]
        if any(keyword in message_lower for keyword in academic_keywords):
            if self.sufficient_info_collected:
                context_analysis["should_recommend"] = True
                context_analysis["confidence"] = 0.7
                context_analysis["recommendation_type"] = "academic_discussion"
                return context_analysis
        
        # User expressing confusion or need for guidance
        confusion_phrases = ["confused", "don't know", "unsure", "help me", "need guidance", "not sure"]
        if any(phrase in message_lower for phrase in confusion_phrases):
            if self.message_count > 3:  # After some conversation
                context_analysis["should_recommend"] = True
                context_analysis["confidence"] = 0.6
                context_analysis["recommendation_type"] = "guidance_needed"
                return context_analysis
        
        return context_analysis

    def _get_dynamic_system_prompt(self):
        """Generate dynamic system prompt based on conversation stage"""
        base_personality = f"""
        You are {self.name}, an expert AI college counselor with deep knowledge of Indian and global education systems. 
        You have years of experience helping students navigate their educational journey.

        Your Core Qualities:
        - Warm, encouraging, and genuinely interested in each student's success
        - Highly knowledgeable about colleges, careers, and education trends
        - Patient listener who asks thoughtful follow-up questions
        - Provides specific, actionable advice rather than generic responses
        - Shares relevant insights and stories to help students understand options
        - Balances dreams with practical realities
        - Proactively provides college recommendations when appropriate based on context

        Current conversation stage: {self.conversation_stage}
        Messages exchanged: {self.message_count}
        Sufficient info collected: {self.sufficient_info_collected}
        
        Based on the conversation, provide helpful, informative responses that guide the student toward making informed decisions about their education and career.
        
        When appropriate (based on conversation context and available student information), 
        proactively provide college recommendations without waiting for explicit requests.
        """
        
        return base_personality

    def _update_conversation_stage(self, user_message):
        """Update conversation stage based on content and message count"""
        message_lower = user_message.lower()
        
        if self.message_count <= 2:
            self.conversation_stage = "greeting"
        elif self.message_count <= 5:
            self.conversation_stage = "information_gathering"
        elif any(word in message_lower for word in ["recommend", "suggest", "what should i", "help me choose"]):
            self.conversation_stage = "recommendation"
        elif self.message_count > 5:
            self.conversation_stage = "detailed_guidance"

    def _extract_student_information(self, user_message: str) -> Dict[str, Any]:
        """Extract and update student information from conversation"""
        message_lower = user_message.lower()
        updates: Dict[str, Any] = {}

        # === Name (very basic placeholder detection, refine with NLP later) ===
        if "my name is" in message_lower:
            name = user_message.split("my name is")[-1].strip().split(" ")[0].title()
            self.student_profile.name = name
            updates["name"] = name

        # === Age ===
        age_match = re.search(r"\b(\d{2})\s*years?\s*old\b", message_lower)
        if age_match:
            age = int(age_match.group(1))
            self.student_profile.age = age
            updates["age"] = age

        # === Academic Performance / Scores ===
        marks_match = re.search(r"(\d{1,3})\s*%|percent", message_lower)
        if marks_match:
            percent = float(marks_match.group(1))
            self.student_profile.academic_performance["overall"] = percent
            self.student_profile.scores["percentage"] = percent
            updates["academic_performance"] = {"overall": percent}

        percentile_match = re.search(r"(\d{1,3})\s*percentile", message_lower)
        if percentile_match:
            perc = float(percentile_match.group(1))
            self.student_profile.scores["percentile"] = perc
            updates["scores"] = {"percentile": perc}

        # === Interests / Preferred Fields ===
        tech_keywords = ["computer", "programming", "software", "coding", "tech", "it"]
        if any(word in message_lower for word in tech_keywords):
            if "Computer Science" not in self.student_profile.preferred_fields:
                self.student_profile.preferred_fields.append("Computer Science")
                self.student_profile.interests.append("Technology")
                updates["preferred_fields"] = self.student_profile.preferred_fields

        medical_keywords = ["doctor", "medical", "medicine", "healthcare", "mbbs"]
        if any(word in message_lower for word in medical_keywords):
            if "Medicine" not in self.student_profile.preferred_fields:
                self.student_profile.preferred_fields.append("Medicine")
                self.student_profile.interests.append("Healthcare")
                updates["preferred_fields"] = self.student_profile.preferred_fields

        business_keywords = ["business", "management", "mba", "finance", "marketing"]
        if any(word in message_lower for word in business_keywords):
            if "Business" not in self.student_profile.preferred_fields:
                self.student_profile.preferred_fields.append("Business")
                self.student_profile.interests.append("Business")
                updates["preferred_fields"] = self.student_profile.preferred_fields

        # === Location Preference ===
        for city in ["delhi", "mumbai", "bangalore", "pune", "hyderabad", "chennai", "kolkata", "indore"]:
            if city in message_lower:
                self.student_profile.location_preference = city.title()
                updates["location_preference"] = city.title()

        # === Budget (₹ or lakh keywords) ===
        budget_match = re.search(r"(\d+(\.\d+)?)\s*(lakh|lakhs|₹)", message_lower)
        if budget_match:
            amount = float(budget_match.group(1))
            if "lakh" in budget_match.group(3):
                amount *= 100000
            self.student_profile.budget = int(amount)
            updates["budget"] = int(amount)

        # === Career Goals ===
        if "research" in message_lower:
            self.student_profile.career_goals.append("Research")
        if "entrepreneur" in message_lower or "startup" in message_lower:
            self.student_profile.career_goals.append("Entrepreneurship")
        if "abroad" in message_lower:
            self.student_profile.career_goals.append("Study Abroad")
        if self.student_profile.career_goals:
            updates["career_goals"] = self.student_profile.career_goals

        # === Extracurricular Activities ===
        if "sports" in message_lower:
            self.student_profile.extracurricular.append("Sports")
        if "music" in message_lower:
            self.student_profile.extracurricular.append("Music")
        if "arts" in message_lower or "drawing" in message_lower:
            self.student_profile.extracurricular.append("Arts")
        if self.student_profile.extracurricular:
            updates["extracurricular"] = self.student_profile.extracurricular

        # === Exams (academic context) ===
        if "jee" in message_lower:
            self.student_profile.additional_info["exam"] = "JEE"
        if "neet" in message_lower:
            self.student_profile.additional_info["exam"] = "NEET"
        if "cat" in message_lower:
            self.student_profile.additional_info["exam"] = "CAT"

        # === Family Background (basic detection) ===
        if "first generation" in message_lower:
            self.student_profile.family_background["education"] = "First Generation Learner"
        if "parents are doctors" in message_lower:
            self.student_profile.family_background["profession"] = "Medical"
        if self.student_profile.family_background:
            updates["family_background"] = self.student_profile.family_background

        # === Mark info collected (removed budget dependency) ===
        if self.student_profile.preferred_fields and self.student_profile.scores:
            self.sufficient_info_collected = True
        
        return updates

    def chat(self, message, context):
        """Main chat function with enhanced recommendation system"""
        self.message_count += 1
        
        # Update conversation stage and extract information
        self._update_conversation_stage(message)
        self._extract_student_information(message)
        
        # Analyze conversation context for recommendations
        context_analysis = self._analyze_conversation_context(message)
        
        # Add to extraction history
        self.extraction_history.append({
            "message": message,
            "stage": self.conversation_stage,
            "context_analysis": context_analysis,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check if we should provide recommendations
        if context_analysis["should_recommend"] and not self.recommendations_provided:
            self.recommendations_provided = True
            response = self.provide_recommendations()
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
        
        # Otherwise proceed with normal chat flow
        if self.use_openai:
            try:
                # Prepare messages for OpenAI
                system_prompt = self._get_dynamic_system_prompt()
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                
                # Add recent conversation context (last 4 exchanges)
                recent_history = self.conversation_history[-8:]  # Last 4 exchanges (user + assistant)
                for i in range(0, len(recent_history)-1, 2):  # Skip current message
                    if i+1 < len(recent_history):
                        messages.insert(-1, {"role": "user", "content": recent_history[i]["content"]})
                        messages.insert(-1, {"role": "assistant", "content": recent_history[i+1]["content"]})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000,
                    frequency_penalty=0.3,
                    presence_penalty=0.2
                )
                
                assistant_response = response.choices[0].message.content
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                assistant_response = self._get_fallback_response(message)
        else:
            assistant_response = self._get_fallback_response(message)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return assistant_response

    def _get_fallback_response(self, message):
        """Provide intelligent fallback responses when OpenAI is not available"""
        message_lower = message.lower()
        
        if self.message_count == 1:
            return f"Hello! I'm {self.name}, your AI college counselor. I'm here to help you navigate your educational journey and find the best college options for your goals. Could you tell me a bit about yourself - what are you currently studying and what fields interest you most?"
        
        # Handle specific queries
        if any(word in message_lower for word in ["engineering", "iit", "jee", "computer science"]):
            return """Great choice! Engineering offers excellent career prospects. Some top options include:

🏆 **IITs** - Premier institutes with world-class education (Admission: JEE Advanced)
🎯 **NITs** - Excellent government institutes across India (Admission: JEE Main)  
⭐ **BITS Pilani** - Top private institute with industry focus (Admission: BITSAT)
🏫 **State colleges** - Good quality education at affordable fees

Computer Science is particularly hot right now with amazing placement opportunities. What's your current academic background? Are you preparing for JEE or any other entrance exams?"""

        elif any(word in message_lower for word in ["medical", "doctor", "neet", "mbbs"]):
            return """Medicine is a noble and rewarding career path! Here's what you should know:

🏥 **AIIMS** - Premier medical institutes with highly subsidized fees
🎓 **Government Medical Colleges** - Affordable with excellent clinical exposure
🏫 **Private Medical Colleges** - Good infrastructure but higher fees (₹50L - ₹1.5Cr)

Key points:
- NEET is mandatory for all medical admissions
- Start preparation early - very competitive field
- Consider specialization options after MBBS
- Alternative paths: BDS, AYUSH, Allied Health Sciences

What's your current academic performance? Have you started NEET preparation?"""

        elif any(word in message_lower for word in ["mba", "management", "business", "cat"]):
            return """Business education opens doors to diverse career opportunities!

🎯 **IIMs** - Top business schools with excellent ROI (Admission: CAT)
⭐ **ISB, XLRI, FMS** - Premier institutes with strong placements  
📈 **Sectoral MBAs** - Healthcare, Rural, Family Business specializations

Career paths:
- Management Consulting (₹15-40L starting)
- Investment Banking & Finance  
- Product Management in Tech
- General Management roles

Most MBA programs prefer 2-3 years work experience. Are you currently working or planning to work before MBA? What business areas interest you most?"""

        elif any(word in message_lower for word in ["confused", "help", "don't know", "unsure"]):
            return """It's completely normal to feel confused about career choices! Let's explore your options systematically.

Let me ask you a few questions to better understand your interests:

🤔 **Academic Performance**: How are your current grades? Which subjects do you enjoy most?
🎯 **Interests**: What activities make you lose track of time? 
💡 **Career Vision**: Where do you see yourself in 10 years?
💰 **Practical Considerations**: Any budget constraints or location preferences?
👨‍👩‍👧‍👦 **Family Input**: What does your family suggest?

Based on your responses, I can provide personalized recommendations. What would you like to share first?"""

        else:
            return """Thank you for sharing that! I'm learning about your preferences and goals.

Based on our conversation so far, I can see you're exploring your options thoughtfully. Here are some areas we could discuss further:

📚 **Academic Paths**: Engineering, Medical, Business, Liberal Arts, Sciences
🌎 **Study Locations**: India vs International options  
💼 **Career Prospects**: Emerging fields vs Traditional stable careers
💰 **Financial Planning**: Education costs, scholarships, loans

What specific aspect would you like to dive deeper into? I'm here to provide detailed insights to help you make informed decisions!"""

    def generate_personalized_recommendations(self, profile=None):
        """Generate recommendations based on student profile using database"""
        recommendations = []
        
        # Use persisted DB profile if provided
        if not profile:
            profile = self.student_profile

        preferred_fields = getattr(profile, "preferred_fields", []) or []
        location_preference = getattr(profile, "location_preference", None)

        # Fetch colleges from database based on preferences
        if preferred_fields:
            # Search for colleges that match preferred fields
            all_colleges = self._search_colleges_by_criteria(
                field_keywords=preferred_fields,
                location=location_preference
            )
        else:
            # Get all colleges if no specific field preference
            all_colleges = self._fetch_colleges_from_database()

        # Filter and score colleges based on student preferences
        for college in all_colleges:
            score = 0
            reasons = []
            
            # Check field alignment
            if preferred_fields:
                college_streams = college.get('streams', [])
                college_courses = college.get('courses', [])
                
                field_match = False
                # Check streams
                if college_streams:
                    field_match = any(
                        any(pref.lower() in stream.lower() for stream in college_streams)
                        for pref in preferred_fields
                    )
                
                # Also check in courses data
                if not field_match and college_courses:
                    for course in college_courses:
                        if isinstance(course, dict):
                            course_category = course.get('Category', '').lower()
                            if any(pref.lower() in course_category for pref in preferred_fields):
                                field_match = True
                                break
                
                if field_match:
                    score += 50
                    reasons.append(f"Offers programs in {', '.join(preferred_fields)}")
            
            # Location preference
            if location_preference:
                if location_preference.lower() in college.get('location', '').lower():
                    score += 25
                    reasons.append("Preferred location")
            
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
            
            if score > 15:  # Minimum threshold
                recommendations.append({
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
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:10] if recommendations else []

    def _initialize_career_insights(self):
        """Initialize career insights database"""
        return {
            "high_growth_careers": {
                "technology": {
                    "Software Engineer": {
                        "description": "Design and develop software applications",
                        "skills_required": ["Programming", "Problem-solving", "System design"],
                        "education_path": ["B.Tech Computer Science", "BCA + MCA", "Self-learning + certifications"],
                        "salary_range": "₹4-50 lakhs per year",
                        "growth_prospects": "Excellent - High demand, startup opportunities, global market"
                    },
                    "Data Scientist": {
                        "description": "Analyze complex data to derive business insights",
                        "skills_required": ["Statistics", "Machine Learning", "Python/R", "SQL"],
                        "education_path": ["B.Tech + Data Science certification", "Statistics/Math degree + upskilling"],
                        "salary_range": "₹6-40 lakhs per year",
                        "growth_prospects": "Very High - Every industry needs data insights"
                    }
                },
                "healthcare": {
                    "Doctor": {
                        "description": "Diagnose and treat medical conditions",
                        "skills_required": ["Medical knowledge", "Empathy", "Decision-making", "Communication"],
                        "education_path": ["MBBS + MD/MS specialization"],
                        "salary_range": "₹6-50+ lakhs per year",
                        "growth_prospects": "Stable - Always in demand"
                    }
                },
                "business": {
                    "Management Consultant": {
                        "description": "Help organizations solve complex business problems",
                        "skills_required": ["Analytical thinking", "Communication", "Industry knowledge"],
                        "education_path": ["Any graduation + MBA from top school"],
                        "salary_range": "₹8-40 lakhs per year",
                        "growth_prospects": "Excellent - High learning curve, global opportunities"
                    }
                }
            }
        }

