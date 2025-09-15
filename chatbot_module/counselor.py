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

class EnhancedDynamicCollegeCounselorBot:
    """Enhanced counselor class with intelligent recommendation system"""

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
        
        # Enhanced field mapping for better course matching
        self.field_mappings = {
            "engineering": ["engineering", "technology", "computer science", "mechanical", "electrical", "civil", "electronics"],
            "medical": ["medicine", "medical", "healthcare", "mbbs", "dental", "pharmacy", "nursing"],
            "business": ["management", "business", "commerce", "finance", "marketing", "economics", "mba"],
            "science": ["science", "physics", "chemistry", "mathematics", "biology", "biotechnology"],
            "arts": ["arts", "humanities", "literature", "history", "psychology", "sociology"],
            "law": ["law", "legal", "judiciary", "llb"],
            "design": ["design", "architecture", "fine arts", "fashion"],
            "agriculture": ["agriculture", "farming", "horticulture", "veterinary"]
        }
        
        # Initialize career insights
        self.career_insights = self._initialize_career_insights()
        
        # Database availability cache
        self.db_stats = self._analyze_database_coverage()

    def _analyze_database_coverage(self) -> Dict[str, Any]:
        """Analyze what data is available in the database"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_colleges,
                COUNT(DISTINCT location) as locations_count,
                COUNT(DISTINCT type) as types_count,
                COUNT(CASE WHEN courses IS NOT NULL THEN 1 END) as colleges_with_courses
            FROM college
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query)).fetchone()
                
                # Get location distribution
                location_query = "SELECT location, COUNT(*) as count FROM college GROUP BY location ORDER BY count DESC LIMIT 10"
                locations = conn.execute(text(location_query)).fetchall()
                
                return {
                    "total_colleges": result[0] if result else 0,
                    "locations_count": result[1] if result else 0,
                    "types_count": result[2] if result else 0,
                    "colleges_with_courses": result[3] if result else 0,
                    "top_locations": [{"location": loc[0], "count": loc[1]} for loc in locations]
                }
                
        except Exception as e:
            logging.error(f"Error analyzing database coverage: {e}")
            return {"total_colleges": 0, "locations_count": 0, "types_count": 0, "colleges_with_courses": 0, "top_locations": []}

    def _extract_comprehensive_requirements(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Extract detailed requirements from current message and conversation history"""
        requirements = {
            "course_field": [],
            "specific_courses": [],
            "location_preferences": [],
            "budget_range": None,
            "college_type": None,
            "entrance_exams": [],
            "specializations": [],
            "priorities": [],
            "just_location_based": False
        }
        
        message_lower = user_message.lower()
        
        # Combine current message with recent conversation for better context
        full_context = message_lower
        if conversation_history:
            recent_messages = [msg["content"].lower() for msg in conversation_history[-6:] if msg["role"] == "user"]
            full_context += " " + " ".join(recent_messages)
        
        # Extract course fields using enhanced mapping
        for field, keywords in self.field_mappings.items():
            if any(keyword in full_context for keyword in keywords):
                requirements["course_field"].append(field)
        
        # Extract specific courses
        specific_courses = [
            "computer science", "mechanical engineering", "electrical engineering", "civil engineering",
            "mbbs", "bds", "pharmacy", "nursing", "physiotherapy",
            "mba", "bba", "bcom", "economics", "ca", "cs",
            "physics", "chemistry", "mathematics", "biotechnology",
            "psychology", "sociology", "political science", "history",
            "llb", "architecture", "fashion design"
        ]
        
        for course in specific_courses:
            if course in full_context:
                requirements["specific_courses"].append(course)
        
        # Extract location preferences
        indian_cities = [
            "delhi", "mumbai", "bangalore", "pune", "hyderabad", "chennai", "kolkata",
            "ahmedabad", "jaipur", "lucknow", "kanpur", "indore", "bhopal", "patna",
            "gurgaon", "noida", "ghaziabad", "kochi", "coimbatore", "madurai",
            "vadodara", "rajkot", "chandigarh", "amritsar", "dehradun", "haridwar"
        ]
        
        indian_states = [
            "maharashtra", "karnataka", "tamil nadu", "gujarat", "rajasthan",
            "uttar pradesh", "madhya pradesh", "bihar", "west bengal", "kerala",
            "punjab", "haryana", "uttarakhand", "himachal pradesh"
        ]
        
        for city in indian_cities:
            if city in full_context:
                requirements["location_preferences"].append(city.title())
        
        for state in indian_states:
            if state in full_context:
                requirements["location_preferences"].append(state.title())
        
        # Check if it's just location-based query
        location_only_phrases = [
            "colleges in", "universities in", "institutes in", "colleges near",
            "best colleges in", "top universities in", "good colleges in"
        ]
        
        if any(phrase in message_lower for phrase in location_only_phrases):
            requirements["just_location_based"] = True
        
        # Extract budget information
        budget_patterns = [
            r"(\d+)\s*(lakh|lakhs)",
            r"₹\s*(\d+)",
            r"under\s*(\d+)",
            r"below\s*(\d+)",
            r"budget.*?(\d+)"
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, full_context)
            if match:
                amount = float(match.group(1))
                if "lakh" in pattern:
                    amount *= 100000
                requirements["budget_range"] = amount
                break
        
        # Extract college type preferences
        if any(word in full_context for word in ["government", "govt", "public"]):
            requirements["college_type"] = "government"
        elif any(word in full_context for word in ["private", "autonomous"]):
            requirements["college_type"] = "private"
        
        # Extract entrance exam context
        entrance_exams = ["jee", "neet", "cat", "gate", "clat", "bitsat", "viteee", "comedk"]
        for exam in entrance_exams:
            if exam in full_context:
                requirements["entrance_exams"].append(exam.upper())
        
        # Extract priorities
        priority_keywords = {
            "placement": ["placement", "job", "salary", "package"],
            "ranking": ["ranking", "top", "best", "prestigious"],
            "fees": ["fees", "affordable", "cheap", "budget"],
            "location": ["location", "city", "near", "hometown"],
            "facilities": ["hostel", "infrastructure", "library", "lab"]
        }
        
        for priority, keywords in priority_keywords.items():
            if any(keyword in full_context for keyword in keywords):
                requirements["priorities"].append(priority)
        
        return requirements

    def _build_smart_database_query(self, requirements: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Build intelligent database query based on requirements"""
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
        WHERE 1=1
        """
        
        params = {}
        query_conditions = []
        
        # Location-based filtering (highest priority)
        if requirements["location_preferences"]:
            location_conditions = []
            for i, location in enumerate(requirements["location_preferences"]):
                param_name = f"location_{i}"
                location_conditions.append(f"LOWER(location) LIKE :{param_name}")
                params[param_name] = f"%{location.lower()}%"
            
            if location_conditions:
                query_conditions.append(f"({' OR '.join(location_conditions)})")
        
        # Course field filtering
        if requirements["course_field"] and not requirements["just_location_based"]:
            course_conditions = []
            
            for i, field in enumerate(requirements["course_field"]):
                field_keywords = self.field_mappings.get(field, [field])
                field_condition_parts = []
                
                for j, keyword in enumerate(field_keywords):
                    param_name = f"field_{i}_{j}"
                    field_condition_parts.append(f"LOWER(courses::text) LIKE :{param_name}")
                    field_condition_parts.append(f"LOWER(type) LIKE :{param_name}")
                    params[param_name] = f"%{keyword.lower()}%"
                
                if field_condition_parts:
                    course_conditions.append(f"({' OR '.join(field_condition_parts)})")
            
            if course_conditions:
                query_conditions.append(f"({' OR '.join(course_conditions)})")
        
        # Specific course filtering
        if requirements["specific_courses"]:
            specific_conditions = []
            for i, course in enumerate(requirements["specific_courses"]):
                param_name = f"specific_course_{i}"
                specific_conditions.append(f"LOWER(courses::text) LIKE :{param_name}")
                params[param_name] = f"%{course.lower()}%"
            
            if specific_conditions:
                query_conditions.append(f"({' OR '.join(specific_conditions)})")
        
        # College type filtering
        if requirements["college_type"]:
            query_conditions.append("LOWER(type) LIKE :college_type")
            params["college_type"] = f"%{requirements['college_type'].lower()}%"
        
        # Add all conditions to query
        if query_conditions:
            query += " AND " + " AND ".join(query_conditions)
        
        # Add ordering
        query += " ORDER BY College_Name"
        
        return query, params

    def _fetch_colleges_with_smart_query(self, requirements: Dict[str, Any]) -> List[Dict]:
        """Fetch colleges using intelligent querying"""
        try:
            query, params = self._build_smart_database_query(requirements)
            
            logging.info(f"Executing query with params: {params}")
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                colleges = []
                
                for row in result:
                    # Parse courses data
                    courses_data = []
                    if row.Courses:
                        try:
                            courses_data = json.loads(row.Courses) if isinstance(row.Courses, str) else row.Courses
                        except (json.JSONDecodeError, TypeError) as e:
                            logging.error(f"Error parsing courses for college {row.College_ID}: {e}")
                            courses_data = []
                    
                    # Extract streams and specializations
                    streams = []
                    specializations = []
                    if courses_data:
                        for course in courses_data:
                            if isinstance(course, dict):
                                category = course.get('Category', '')
                                if category and category not in streams:
                                    streams.append(category)
                                
                                # Extract specializations from course names or descriptions
                                course_name = course.get('Course', '')
                                if course_name and course_name not in specializations:
                                    specializations.append(course_name)
                    
                    # Calculate relevance score based on requirements
                    relevance_score = self._calculate_relevance_score(
                        {
                            'location': row.Location,
                            'type': row.Type,
                            'courses': courses_data,
                            'streams': streams
                        },
                        requirements
                    )
                    
                    college_data = {
                        "id": row.College_ID,
                        "name": row.College_Name or row.Name,
                        "location": row.Location or "Not specified",
                        "type": row.Type or "General",
                        "affiliation": row.Affiliation or "Not specified",
                        "website": row.Website,
                        "contact": row.Contact,
                        "email": row.Email,
                        "courses": courses_data,
                        "streams": streams,
                        "specializations": specializations,
                        "admission": row.Admission_Process or "Various entrance exams",
                        "scholarship": row.Scholarship or "Available",
                        "fees": self._extract_fees_from_courses(courses_data),
                        "highlights": self._generate_highlights(row._asdict()),
                        "relevance_score": relevance_score
                    }
                    colleges.append(college_data)
                
                # Sort by relevance score
                colleges.sort(key=lambda x: x['relevance_score'], reverse=True)
                return colleges
                
        except Exception as e:
            logging.error(f"Error fetching colleges with smart query: {e}")
            return []

    def _calculate_relevance_score(self, college_data: Dict, requirements: Dict[str, Any]) -> float:
        """Calculate relevance score for a college based on requirements"""
        score = 0.0
        
        # Location match (30% weight)
        if requirements["location_preferences"]:
            location_match = any(
                loc.lower() in college_data.get('location', '').lower() 
                for loc in requirements["location_preferences"]
            )
            if location_match:
                score += 30
        
        # Course field match (40% weight)
        if requirements["course_field"]:
            field_match = False
            college_streams = [stream.lower() for stream in college_data.get('streams', [])]
            
            for field in requirements["course_field"]:
                field_keywords = self.field_mappings.get(field, [field])
                if any(keyword in ' '.join(college_streams) for keyword in field_keywords):
                    field_match = True
                    break
            
            if field_match:
                score += 40
        
        # Specific course match (25% weight)
        if requirements["specific_courses"]:
            course_match = False
            courses_text = json.dumps(college_data.get('courses', [])).lower()
            
            for course in requirements["specific_courses"]:
                if course.lower() in courses_text:
                    course_match = True
                    break
            
            if course_match:
                score += 25
        
        # College type match (5% weight)
        if requirements["college_type"]:
            if requirements["college_type"].lower() in college_data.get('type', '').lower():
                score += 5
        
        return score

    def _generate_llm_fallback_response(self, requirements: Dict[str, Any], db_results_count: int) -> str:
        """Generate LLM response when database results are insufficient"""
        context_info = {
            "requirements": requirements,
            "db_results_count": db_results_count,
            "db_stats": self.db_stats
        }
        
        if self.use_openai:
            try:
                fallback_prompt = f"""
                The user is looking for college recommendations with the following requirements:
                - Course Fields: {requirements.get('course_field', [])}
                - Specific Courses: {requirements.get('specific_courses', [])}
                - Location Preferences: {requirements.get('location_preferences', [])}
                - Budget Range: {requirements.get('budget_range')}
                - College Type: {requirements.get('college_type')}
                - Just Location Based: {requirements.get('just_location_based')}
                
                Our database only returned {db_results_count} colleges matching these criteria.
                
                Please provide comprehensive college recommendations for these requirements, including:
                1. Top colleges that match their criteria
                2. Alternative options if their preferences are too specific
                3. Practical advice about entrance exams, fees, and admission process
                4. Suggestions for broadening their search if needed
                
                Be specific with college names, locations, and admission requirements. Focus on Indian colleges and education system.
                """
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert Indian college counselor with comprehensive knowledge of Indian colleges and universities."},
                        {"role": "user", "content": fallback_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logging.error(f"LLM fallback error: {e}")
                return self._get_static_fallback_response(requirements)
        else:
            return self._get_static_fallback_response(requirements)

    def _get_static_fallback_response(self, requirements: Dict[str, Any]) -> str:
        """Provide static fallback when both DB and LLM are unavailable"""
        if requirements.get('course_field'):
            primary_field = requirements['course_field'][0]
            
            if primary_field == "engineering":
                return """Here are top engineering college recommendations:

🏆 **Premier Institutes (IITs)**
- IIT Delhi, Mumbai, Bangalore, Kharagpur
- Admission: JEE Advanced
- Fees: ₹2-3 lakhs per year

🎯 **Excellent Government Colleges (NITs)**  
- NIT Trichy, Warangal, Surathkal, Calicut
- Admission: JEE Main
- Fees: ₹1-2 lakhs per year

⭐ **Top Private Colleges**
- BITS Pilani, VIT, Manipal, SRM
- Admission: Own entrance exams
- Fees: ₹3-4 lakhs per year

Would you like specific information about any of these colleges or help with entrance exam preparation?"""

            elif primary_field == "medical":
                return """Top medical college recommendations:

🏥 **AIIMS Institutes**
- AIIMS Delhi, Jodhpur, Bhubaneswar, Rishikesh
- Admission: NEET + AIIMS MBBS
- Fees: ₹5,000 per year (highly subsidized)

🎓 **Government Medical Colleges**
- MAMC Delhi, GMC Chandigarh, KMC Manipal
- Admission: NEET
- Fees: ₹50,000-2 lakhs per year

🏫 **Reputed Private Medical Colleges**
- CMC Vellore, Kasturba Medical College
- Admission: NEET
- Fees: ₹10-25 lakhs total

NEET is mandatory for all medical admissions. Start preparation early as it's highly competitive!"""

        location_text = ""
        if requirements.get('location_preferences'):
            locations = ", ".join(requirements['location_preferences'])
            location_text = f" in {locations}"
        
        return f"""I understand you're looking for colleges{location_text}. While I don't have specific database results for your exact criteria, here's some general guidance:

📍 **For your preferred location{location_text}:**
- Check state government colleges for affordable quality education
- Look into deemed universities for diverse course options
- Consider autonomous colleges for academic flexibility

🔍 **Recommended Next Steps:**
1. Visit official state education websites
2. Check NIRF rankings for quality assessment
3. Attend college fairs and virtual sessions
4. Connect with current students/alumni

💡 **Broaden Your Search:**
- Consider nearby cities/states
- Look into online/hybrid programs
- Explore scholarship opportunities

Would you like me to help you refine your search criteria or provide information about entrance exams and admission processes?"""

    def generate_enhanced_recommendations(self, user_message: str, conversation_history: List[Dict]) -> str:
        """Enhanced recommendation system with intelligent fallback"""
        
        # Extract comprehensive requirements
        requirements = self._extract_comprehensive_requirements(user_message, conversation_history)
        
        logging.info(f"Extracted requirements: {requirements}")
        
        # Fetch colleges from database
        db_colleges = self._fetch_colleges_with_smart_query(requirements)
        
        # Determine if we have sufficient results
        min_results_threshold = 3
        has_sufficient_results = len(db_colleges) >= min_results_threshold
        
        if has_sufficient_results:
            return self._format_database_recommendations(db_colleges, requirements)
        else:
            # Use LLM fallback for comprehensive recommendations
            llm_response = self._generate_llm_fallback_response(requirements, len(db_colleges))
            
            # If we have some database results, append them
            if db_colleges:
                db_section = self._format_database_recommendations(db_colleges, requirements, is_supplementary=True)
                return f"{llm_response}\n\n---\n\n**Additional colleges from our database:**\n{db_section}"
            else:
                return llm_response

    def _format_database_recommendations(self, colleges: List[Dict], requirements: Dict[str, Any], is_supplementary: bool = False) -> str:
        """Format database results into readable recommendations"""
        if not colleges:
            return "No colleges found matching your specific criteria."
        
        header = "Here are college recommendations from our database:" if not is_supplementary else "Colleges matching your criteria:"
        
        response = f"📚 **{header}**\n\n"
        
        for i, college in enumerate(colleges[:8], 1):  # Limit to top 8 results
            response += f"**{i}. {college['name']}**\n"
            response += f"📍 Location: {college['location']}\n"
            
            if college['streams']:
                response += f"🎓 Programs: {', '.join(college['streams'][:3])}\n"
            
            if college.get('fees', 0) > 0:
                fees_text = f"₹{college['fees']:,}" if college['fees'] >= 1000 else f"₹{college['fees']:,}K"
                response += f"💰 Fees: ~{fees_text} per year\n"
            
            if college['admission']:
                response += f"📝 Admission: {college['admission']}\n"
            
            if college['highlights']:
                response += f"⭐ Highlights: {', '.join(college['highlights'][:2])}\n"
            
            if college.get('website'):
                response += f"🌐 Website: {college['website']}\n"
            
            response += f"🎯 Match Score: {college['relevance_score']:.0f}%\n\n"
        
        # Add summary and next steps
        if not is_supplementary:
            response += self._add_recommendation_summary(requirements, len(colleges))
        
        return response

    def _add_recommendation_summary(self, requirements: Dict[str, Any], total_results: int) -> str:
        """Add summary and next steps to recommendations"""
        summary = f"**Summary:** Found {total_results} colleges matching your preferences.\n\n"
        
        if requirements.get('course_field'):
            summary += f"✅ Focused on {', '.join(requirements['course_field'])} programs\n"
        
        if requirements.get('location_preferences'):
            summary += f"✅ Prioritized locations: {', '.join(requirements['location_preferences'])}\n"
        
        summary += "\n**Next Steps:**\n"
        summary += "1. Research top 3-5 colleges in detail\n"
        summary += "2. Check specific admission requirements\n"
        summary += "3. Visit college websites and attend virtual tours\n"
        summary += "4. Prepare for required entrance exams\n\n"
        
        summary += "Would you like more details about any specific college or help with entrance exam preparation?"
        
        return summary

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

    def generate_personalized_recommendations(self, profile=None):
        """Generate recommendations based on student profile using database"""
        recommendations = []
        
        # Use persisted DB profile if provided, otherwise use current profile
        if not profile:
            profile = self.student_profile

        preferred_fields = getattr(profile, "preferred_fields", []) or []
        location_preference = getattr(profile, "location_preference", None)

        # Extract requirements similar to enhanced recommendations
        requirements = {
            "course_field": [field.lower() for field in preferred_fields],
            "specific_courses": [],
            "location_preferences": [location_preference] if location_preference else [],
            "budget_range": getattr(profile, "budget", None),
            "college_type": None,
            "entrance_exams": [],
            "specializations": [],
            "priorities": [],
            "just_location_based": False
        }

        # Fetch colleges using the smart query system
        db_colleges = self._fetch_colleges_with_smart_query(requirements)

        # Convert to the expected format for backwards compatibility
        for college in db_colleges:
            score = college.get('relevance_score', 0)
            reasons = []
            
            # Build match reasons based on score components
            if requirements["course_field"]:
                if any(field in str(college.get('streams', [])).lower() for field in requirements["course_field"]):
                    reasons.append(f"Offers programs in {', '.join(preferred_fields)}")
            
            if location_preference:
                if location_preference.lower() in college.get('location', '').lower():
                    reasons.append("Preferred location")
            
            if college.get('scholarship') and college.get('scholarship').lower() != "n/a":
                reasons.append("Scholarships available")
                
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

    # Initialize career insights
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

    def _analyze_conversation_context(self, user_message: str) -> Dict[str, Any]:
        """Analyze conversation context to determine if recommendations are appropriate"""
        message_lower = user_message.lower()
        context_analysis = {
            "should_recommend": False,
            "recommendation_type": None,
            "confidence": 0.0
        }
        
        # Direct requests for recommendations
        direct_triggers = ["recommend", "suggest", "college", "university", "institute"]
        if any(trigger in message_lower for trigger in direct_triggers):
            context_analysis["should_recommend"] = True
            context_analysis["confidence"] = 0.9
            context_analysis["recommendation_type"] = "direct_request"
            return context_analysis
        
        # Contextual triggers based on conversation stage
        if self.conversation_stage in ["recommendation", "detailed_guidance"]:
            # Questions about options/choices
            option_questions = ["what should i", "which one", "options", "choices", "what are"]
            if any(question in message_lower for question in option_questions):
                context_analysis["should_recommend"] = True
                context_analysis["confidence"] = 0.8
                context_analysis["recommendation_type"] = "option_inquiry"
                return context_analysis
        
        # Academic/career discussions with sufficient profile info
        academic_keywords = ["study", "course", "degree", "program", "career", "future"]
        if any(keyword in message_lower for keyword in academic_keywords):
            if self.sufficient_info_collected:
                context_analysis["should_recommend"] = True
                context_analysis["confidence"] = 0.7
                context_analysis["recommendation_type"] = "academic_discussion"
                return context_analysis
        
        # User expressing confusion or need for guidance
        confusion_phrases = ["confused", "don't know", "unsure", "help me", "need guidance"]
        if any(phrase in message_lower for phrase in confusion_phrases):
            if self.message_count > 3:  # After some conversation
                context_analysis["should_recommend"] = True
                context_analysis["confidence"] = 0.6
                context_analysis["recommendation_type"] = "guidance_needed"
                return context_analysis
        
        return context_analysis

    def chat(self, message, context):
        """Enhanced chat function with improved recommendation system"""
        self.message_count += 1
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check if this is a recommendation request
        message_lower = message.lower()
        recommendation_triggers = [
            "recommend", "suggest", "college", "university", "institute",
            "which college", "best colleges", "colleges in", "help me choose"
        ]
        
        is_recommendation_request = any(trigger in message_lower for trigger in recommendation_triggers)
        
        if is_recommendation_request:
            # Generate enhanced recommendations
            response = self.generate_enhanced_recommendations(message, self.conversation_history)
        else:
            # Use regular chat functionality
            if self.use_openai:
                try:
                    system_prompt = self._get_dynamic_system_prompt()
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ]
                    
                    # Add recent conversation context
                    recent_history = self.conversation_history[-6:]
                    for msg in recent_history[:-1]:  # Exclude current message
                        messages.insert(-1, {"role": msg["role"], "content": msg["content"]})
                    
                    openai_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    response = openai_response.choices[0].message.content
                    
                except Exception as e:
                    logging.error(f"OpenAI API error: {e}")
                    response = self._get_fallback_response(message)
            else:
                response = self._get_fallback_response(message)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response

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
        - Uses enhanced recommendation system when students need college suggestions

        Current conversation stage: {self.conversation_stage}
        Messages exchanged: {self.message_count}
        Database coverage: {self.db_stats['total_colleges']} colleges available
        
        Provide helpful, informative responses that guide students toward making informed decisions.
        When students ask about colleges, use the enhanced recommendation system that intelligently
        searches the database and provides LLM fallback when needed.
        """
        
        return base_personality

    def _get_fallback_response(self, message):
        """Provide intelligent fallback responses when OpenAI is not available"""
        message_lower = message.lower()
        
        if self.message_count == 1:
            return f"Hello! I'm {self.name}, your AI college counselor. I'm here to help you navigate your educational journey and find the best college options for your goals. Could you tell me a bit about yourself - what are you currently studying and what fields interest you most?"
        
        # Handle specific queries with enhanced responses
        if any(word in message_lower for word in ["engineering", "iit", "jee", "computer science"]):
            return """Engineering offers excellent career prospects. Let me help you with some recommendations:

**Premier Institutes (IITs)**
- IIT Delhi, Mumbai, Bangalore, Kharagpur, Kanpur
- Admission: JEE Advanced (need JEE Main qualification first)
- Fees: ₹2-3 lakhs per year
- Placement: ₹10-50+ lakhs average packages

**National Institutes of Technology (NITs)**
- NIT Trichy, Warangal, Surathkal, Calicut, Allahabad
- Admission: JEE Main
- Fees: ₹1.5-2 lakhs per year
- Great balance of quality and affordability

**Top Private Engineering Colleges**
- BITS Pilani, VIT Vellore, Manipal Institute, SRM
- Own entrance exams (BITSAT, VITEEE, etc.)
- Fees: ₹3-4 lakhs per year
- Strong industry connections

Would you like specific information about any particular branch of engineering or help with entrance exam strategy? I can also recommend colleges based on your location preferences!"""

        elif any(word in message_lower for word in ["medical", "doctor", "neet", "mbbs"]):
            return """Medicine is a noble career path! Here's comprehensive guidance:

**AIIMS (All India Institute of Medical Sciences)**
- AIIMS Delhi, Jodhpur, Bhubaneswar, Rishikesh, and others
- Admission: NEET UG (extremely competitive)
- Fees: ₹5,564 per year (highly subsidized)
- Best medical education in India

**Government Medical Colleges**
- State quotas available (85% seats reserved for state students)
- Examples: MAMC Delhi, GMC Chandigarh, KMC Mangalore
- Fees: ₹10K-2 lakhs per year
- Excellent clinical exposure

**Deemed Medical Universities**
- CMC Vellore, Kasturba Medical College, St. John's
- All India quota seats available
- Fees: ₹10-25 lakhs total course
- Good infrastructure and research opportunities

**Private Medical Colleges** (₹50L-1.5Cr total fees)

Key points:
- NEET is mandatory - start preparation in Class 11
- Consider AIIMS, JIPMER for best value
- 15% All India quota in government colleges
- Look into state counseling for better chances

What's your current academic level? Are you preparing for NEET?"""

        elif any(word in message_lower for word in ["mba", "management", "business", "cat"]):
            return """Business education opens diverse career opportunities!

**Indian Institutes of Management (IIMs)**
- IIM A, B, C (top tier), IIM L, I, K (excellent newer ones)
- Admission: CAT + Personal Interview
- Fees: ₹20-25 lakhs total
- Placements: ₹25-35 lakhs average, consulting/finance roles

**Other Premier B-Schools**
- ISB Hyderabad/Mohali (1-year MBA)
- XLRI Jamshedpur, FMS Delhi, IIFT Delhi
- Various entrance exams (XAT, IIFT, etc.)
- Strong industry reputation

**Specialization Options**
- General Management, Finance, Marketing
- Operations, HR, Healthcare Management
- Family Business, Rural Management

**Career Paths Post-MBA:**
- Management Consulting (₹15-40L starting)
- Investment Banking & Finance
- Product Management (Tech companies)
- General Management roles

Most top MBAs prefer 2-3 years work experience. Are you currently working or planning to gain experience first? What business areas interest you most?"""

        elif any(word in message_lower for word in ["confused", "help", "don't know", "unsure", "recommend"]):
            # This might trigger the enhanced recommendation system
            return """I understand the confusion - choosing the right college is a big decision! Let me help you systematically.

To provide the best recommendations, I'd like to understand:

**Your Academic Background:**
- Which class/year are you in?
- What subjects do you enjoy most?
- Your approximate academic performance?

**Career Interests:**
- Any specific fields that excite you? (Tech, Healthcare, Business, Arts)
- Are you drawn to problem-solving, creativity, helping people, or business?

**Practical Considerations:**
- Preferred locations for study?
- Any budget constraints?
- Family expectations or suggestions?

**Study Preferences:**
- Large universities vs smaller colleges?
- Research-focused vs industry-oriented programs?

Once I know more about your preferences, I can provide specific college recommendations from our database and suggest the best paths forward. 

What would you like to share first? Even partial information helps me guide you better!"""

        else:
            return """Thank you for sharing that information! I'm building a comprehensive understanding of your goals and preferences.

Based on our conversation, here are some areas we can explore further:

**Academic Paths We Can Discuss:**
- Engineering & Technology (various specializations)
- Medical & Healthcare Sciences
- Business & Management Studies
- Science & Research
- Arts, Design & Creative Fields
- Law & Social Sciences

**Geographic Options:**
- Top colleges across different Indian states
- Metro vs non-metro college experiences
- International study opportunities

**Career Trajectory Planning:**
- Industry trends and job market insights
- Skills development alongside academics
- Internship and placement guidance

**Practical Guidance:**
- Entrance exam strategies
- Application processes and deadlines
- Scholarship and financial aid options

What specific aspect would you like to dive deeper into? I can provide detailed recommendations based on your interests and circumstances!"""

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

        # Enhanced information extraction with better patterns
        
        # === Name ===
        name_patterns = [
            r"my name is (\w+)",
            r"i am (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).title()
                self.student_profile.name = name
                updates["name"] = name
                break

        # === Age and Academic Level ===
        age_patterns = [
            r"(\d{1,2})\s*years?\s*old",
            r"age\s*is\s*(\d{1,2})",
            r"i am (\d{1,2})"
        ]
        for pattern in age_patterns:
            match = re.search(pattern, message_lower)
            if match:
                age = int(match.group(1))
                if 15 <= age <= 25:  # Reasonable age range for students
                    self.student_profile.age = age
                    updates["age"] = age
                break

        # Class/Year detection
        class_patterns = [
            r"class\s*(\d{1,2})",
            r"(\d{1,2})th\s*class",
            r"grade\s*(\d{1,2})",
            r"std\s*(\d{1,2})"
        ]
        for pattern in class_patterns:
            match = re.search(pattern, message_lower)
            if match:
                class_num = int(match.group(1))
                self.student_profile.additional_info["class"] = class_num
                updates["class"] = class_num
                break

        # === Academic Performance ===
        performance_patterns = [
            r"(\d{1,3}\.?\d*)\s*%",
            r"(\d{1,3}\.?\d*)\s*percent",
            r"scored?\s*(\d{1,3}\.?\d*)",
            r"marks?\s*(\d{1,3}\.?\d*)"
        ]
        for pattern in performance_patterns:
            match = re.search(pattern, message_lower)
            if match:
                score = float(match.group(1))
                if score <= 100:  # Percentage
                    self.student_profile.academic_performance["overall"] = score
                    self.student_profile.scores["percentage"] = score
                    updates["academic_performance"] = {"overall": score}
                break

        # === Enhanced Interest Detection ===
        interest_mappings = {
            "technology": ["computer", "programming", "software", "coding", "tech", "it", "artificial intelligence", "ai", "machine learning"],
            "medical": ["doctor", "medical", "medicine", "healthcare", "mbbs", "surgery", "patient", "hospital"],
            "business": ["business", "management", "mba", "finance", "marketing", "entrepreneur", "startup"],
            "engineering": ["engineering", "engineer", "mechanical", "electrical", "civil", "chemical"],
            "science": ["physics", "chemistry", "mathematics", "biology", "research", "scientist"],
            "arts": ["arts", "creative", "design", "drawing", "painting", "music", "literature"],
            "law": ["law", "lawyer", "legal", "court", "justice", "advocate"]
        }

        for field, keywords in interest_mappings.items():
            if any(keyword in message_lower for keyword in keywords):
                if field not in [f.lower() for f in self.student_profile.preferred_fields]:
                    field_name = field.title()
                    if field == "technology":
                        field_name = "Computer Science"
                    elif field == "medical":
                        field_name = "Medicine"
                    elif field == "business":
                        field_name = "Business"
                    
                    self.student_profile.preferred_fields.append(field_name)
                    self.student_profile.interests.append(field.title())
                    updates["preferred_fields"] = self.student_profile.preferred_fields

        # === Location Preferences (Enhanced) ===
        location_indicators = [
            r"in (\w+)",
            r"near (\w+)",
            r"from (\w+)",
            r"prefer (\w+)",
            r"want to study in (\w+)"
        ]
        
        indian_locations = {
            # Major cities
            "delhi", "mumbai", "bangalore", "pune", "hyderabad", "chennai", "kolkata",
            "ahmedabad", "jaipur", "lucknow", "kanpur", "indore", "bhopal", "patna",
            "gurgaon", "noida", "ghaziabad", "kochi", "coimbatore", "madurai",
            
            # States
            "maharashtra", "karnataka", "tamil nadu", "gujarat", "rajasthan",
            "uttar pradesh", "madhya pradesh", "bihar", "west bengal", "kerala",
            "punjab", "haryana", "uttarakhand", "himachal pradesh"
        }
        
        for location in indian_locations:
            if location in message_lower:
                self.student_profile.location_preference = location.title()
                updates["location_preference"] = location.title()
                break

        # === Budget Detection (Enhanced) ===
        budget_patterns = [
            r"budget.*?(\d+(?:\.\d+)?)\s*(lakh|lakhs)",
            r"afford.*?(\d+(?:\.\d+)?)\s*(lakh|lakhs)",
            r"₹\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs)?",
            r"around.*?(\d+(?:\.\d+)?)\s*(lakh|lakhs)",
            r"under.*?(\d+(?:\.\d+)?)\s*(lakh|lakhs)"
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount = float(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                
                if "lakh" in unit.lower():
                    amount *= 100000
                elif amount < 100:  # Assume lakhs if number is small
                    amount *= 100000
                    
                self.student_profile.budget = int(amount)
                updates["budget"] = int(amount)
                break

        # === Career Goals (Enhanced) ===
        career_keywords = {
            "research": ["research", "scientist", "phd", "academic"],
            "entrepreneurship": ["entrepreneur", "startup", "business owner", "own company"],
            "corporate": ["corporate", "mnc", "company job", "placement"],
            "government": ["government job", "civil service", "upsc", "ssc"],
            "international": ["abroad", "international", "foreign", "global"]
        }

        for goal, keywords in career_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if goal not in [g.lower() for g in self.student_profile.career_goals]:
                    self.student_profile.career_goals.append(goal.title())
                    updates["career_goals"] = self.student_profile.career_goals

        # === Check if sufficient info is collected ===
        if (self.student_profile.preferred_fields and 
            (self.student_profile.scores or self.student_profile.academic_performance)):
            self.sufficient_info_collected = True
        
        return updates