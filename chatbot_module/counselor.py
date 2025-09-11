from datetime import datetime
from chatbot_module.models import StudentConversation, DynamicStudentProfile
from chatbot_module.college_database import _initialize_comprehensive_college_database
import logging
import re
from typing import Dict, Any

class DynamicCollegeCounselorBot:
    """Enhanced counselor class for FastAPI integration"""

    def __init__(self, api_key=None, name="Lauren"):
        self.name = name

        self.model = "gpt-4o"
        
        # Initialize OpenAI client if API key is provided
        if api_key:
            try:
                logging.info("Openai started")
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
        
        # Initialize knowledge bases
        self.college_database = _initialize_comprehensive_college_database()
        self.career_insights = self._initialize_career_insights()

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

        Current conversation stage: {self.conversation_stage}
        Messages exchanged: {self.message_count}
        
        Based on the conversation, provide helpful, informative responses that guide the student toward making informed decisions about their education and career.
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
        logging.info(f"Extracting info from message: {user_message}")
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
        logging.info(f" marks_match: {marks_match}")
        if marks_match:
            logging.info(f"Marks match found: {marks_match}")
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
        for city in ["delhi", "mumbai", "bangalore", "pune", "hyderabad", "chennai", "kolkata"]:
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
        
        logging.info(f"Extracted student info updates: {updates}")
        return updates


    def chat(self, message, context):
        """Main chat function with OpenAI integration"""
        self.message_count += 1
        
        # Update conversation stage and extract information
        self._update_conversation_stage(message)
        logging.info(f"message:{message}")
        self._extract_student_information(message)
        
        # Add to extraction history
        self.extraction_history.append({
            "message": message,
            "stage": self.conversation_stage,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
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
🌍 **Study Locations**: India vs International options  
💼 **Career Prospects**: Emerging fields vs Traditional stable careers
💰 **Financial Planning**: Education costs, scholarships, loans

What specific aspect would you like to dive deeper into? I'm here to provide detailed insights to help you make informed decisions!"""

    def generate_personalized_recommendations(self, profile=None):
        """Generate recommendations based on student profile (budget removed from scoring)"""
        recommendations = []
        
        # ✅ Use persisted DB profile if provided
        if not profile:
            profile = self.student_profile  # fallback

        preferred_fields = getattr(profile, "preferred_fields", []) or []
        location_preference = getattr(profile, "location_preference", None)
        # Removed budget parameter - budget = getattr(profile, "budget", None)

        # Get all colleges from database
        all_colleges = []
        for category in self.college_database.values():
            all_colleges.extend(category)
        
        # Filter and score colleges based on student preferences (without budget)
        for college in all_colleges:
            score = 0
            reasons = []
            
            # Check field alignment
            if preferred_fields:
                college_streams = college.get('streams', [])
                field_match = any(
                    any(pref.lower() in stream.lower() for stream in college_streams)
                    for pref in preferred_fields
                )
                if field_match:
                    score += 50  # Increased weight since budget is removed
                    reasons.append(f"Offers programs in {', '.join(preferred_fields)}")
            
            # Budget consideration removed completely
            # No budget-based scoring or filtering
            
            # Location preference
            if location_preference:
                if location_preference.lower() in college.get('location', '').lower():
                    score += 25  # Increased weight since budget is removed
                    reasons.append("Preferred location")
            
            # Add base score for quality (based on highlights)
            score += len(college.get('highlights', [])) * 3  # Increased weight
            
            if score > 15:  # Adjusted threshold since budget scoring is removed
                recommendations.append({
                    "name": college['name'],
                    "location": college['location'],
                    "fees": college.get('fees', 0),  # Still display fees for information
                    "match_score": min(score, 100.0),
                    "match_reasons": reasons or ["Good overall fit based on your profile"],
                    "type": college.get('type', 'General'),
                    "admission": college.get('admission', 'Various entrance exams'),
                    "highlights": college.get('highlights', [])[:3]  # Top 3 highlights
                })
        
        # Sort by match score and return top recommendations
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
       
        return recommendations[:10] if recommendations else []