from sqlalchemy.orm import Session
from datetime import datetime
import logging
import re

from chatbot_module.schemas import CollegeRecommendation, Title
from chatbot_module.chat_manager import ChatManager
from chatbot_module.message_manager import MessageManager
from chatbot_module.recommendation.college_counselor import DynamicCollegeCounselorBot
from chatbot_module.recommendation_manager import RecommendationManager
from chatbot_module.profile_manager import ProfileManager
from chatbot_module.config import OPENAI_API_KEY
from openai import OpenAI

# -------------------- OpenAI Client --------------------
client = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

class BotManager:
    """Manages chatbot interactions and database logging"""

    def __init__(self, db: Session):
        self.db = db
        self.bot = DynamicCollegeCounselorBot(api_key=OPENAI_API_KEY)  # AI model
        self.message_manager = MessageManager(db)
        self.recommendation_manager = RecommendationManager(db)
        self.profile_manager = ProfileManager(db)

    def _generate_chat_title(self, chat_id: str, first_message: str) -> str:
        """Generate a title for the chat using OpenAI and store it if not exists."""
        existing_title = self.db.query(Title).filter(Title.chat_id == chat_id).first()
        if existing_title:
            return existing_title.title  # ✅ Already exists

        # 🔥 Use OpenAI to generate title
        try:
            # Use chat completions instead of responses.create
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate a very short title (max 5 words) summarizing the conversation topic."},
                    {"role": "user", "content": first_message}
                ],
                max_tokens=15
            )
            title_text = response.choices[0].message.content.strip().strip('"')
            logging.info(f"Title: {title_text}")

            # ✅ Save into DB
            new_title = Title(chat_id=chat_id, title=title_text, created_at=datetime.utcnow())
            self.db.add(new_title)
            self.db.commit()
            self.db.refresh(new_title)

            return new_title.title
        except Exception as e:
            logging.error(f"Error generating chat title: {e}")
            # Fallback title based on message content
            if "hello" in first_message.lower() or "hi" in first_message.lower():
                fallback_title = "Greeting"
            else:
                fallback_title = "College Counseling"
                
            new_title = Title(chat_id=chat_id, title=fallback_title, created_at=datetime.utcnow())
            self.db.add(new_title)
            self.db.commit()
            return fallback_title

    def _should_generate_recommendations(self, message_text: str, response_text: str) -> bool:
        """Determine if we should generate college recommendations based on context"""
        message_lower = message_text.lower()
        response_lower = response_text.lower()
        
        # Check if user is explicitly asking for recommendations
        recommendation_keywords = [
            "recommend", "suggest", "college", "university", "institute", 
            "where should i study", "which college", "admission", "apply",
            "computer science", "engineering", "medical", "mba", "degree",
            "course", "program", "study", "education", "options", "choices"
        ]
        
        # Don't generate recommendations for simple greetings
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        
        if any(keyword in message_lower for keyword in greeting_keywords):
            return False
            
        # Check if bot response contains recommendations
        if any(keyword in response_lower for keyword in ["recommendation", "college", "university", "institute", "🎓", "📍"]):
            return True
            
        return any(keyword in message_lower for keyword in recommendation_keywords)

    def _store_recommendations(self, chat_id: str, recommendations: list):
        """Store recommendations in the database"""
        if not recommendations:
            return
            
        # Clear existing recommendations first
        self.recommendation_manager.clear_recommendations(chat_id)
        
        # Store new recommendations - only if they have valid data
        valid_recommendations = []
        for rec in recommendations:
            if (isinstance(rec, dict) and rec.get('name') and 
                rec['name'] != 'Unknown College' and rec['name'] is not None):
                valid_recommendations.append(rec)
        
        if not valid_recommendations:
            logging.warning("No valid recommendations to store")
            return
            
        for rec in valid_recommendations:
            # Convert lists to strings for database storage
            match_reasons = ', '.join(rec.get('match_reasons', [])) if rec.get('match_reasons') else 'Good fit'
            highlights = ', '.join(rec.get('highlights', [])) if rec.get('highlights') else 'Quality education'
            
            # Create recommendation object
            new_rec = CollegeRecommendation(
                chat_id=chat_id,
                name=rec.get('name', 'Unknown College'),
                location=rec.get('location', 'Not specified'),
                match_score=rec.get('match_score', 0),
                match_reasons=match_reasons,
                college_type=rec.get('type', 'General'),
                admission=rec.get('admission', 'Various entrance exams'),
                highlights=highlights,
                website=rec.get('website', ''),
                contact=rec.get('contact', ''),
                email=rec.get('email', ''),
                scholarship=rec.get('scholarship', 'Available'),
                affiliation=rec.get('affiliation', 'Not specified'),
                created_at=datetime.utcnow()
            )
            self.db.add(new_rec)
        
        self.db.commit()

    def _format_recommendations_for_response(self, recommendations: list) -> list:
        """Format recommendations for API response"""
        if not recommendations:
            return []
            
        formatted_recs = []
        for rec in recommendations:
            if hasattr(rec, 'name'):  # Database object
                formatted_recs.append({
                    "name": rec.name,
                    "location": rec.location,
                    "match_score": rec.match_score,
                    "match_reasons": rec.match_reasons.split(', ') if rec.match_reasons else [],
                    "type": rec.college_type,
                    "admission": rec.admission,
                    "highlights": rec.highlights.split(', ') if rec.highlights else [],
                    "website": rec.website,
                    "contact": rec.contact,
                    "email": rec.email,
                    "scholarship": rec.scholarship,
                    "affiliation": rec.affiliation
                })
            elif isinstance(rec, dict):  # Direct dict from bot
                formatted_recs.append({
                    "name": rec.get('name'),
                    "location": rec.get('location', 'Not specified'),
                    "match_score": rec.get('match_score', 0),
                    "match_reasons": rec.get('match_reasons', []),
                    "type": rec.get('type', 'General'),
                    "admission": rec.get('admission', 'Various entrance exams'),
                    "highlights": rec.get('highlights', []),
                    "website": rec.get('website', ''),
                    "contact": rec.get('contact', ''),
                    "email": rec.get('email', ''),
                    "scholarship": rec.get('scholarship', 'Available'),
                    "affiliation": rec.get('affiliation', 'Not specified')
                })
        
        return formatted_recs

    def process_message(self, user_id: str, chat_id: str, message_text: str):
        # ✅ Validate chat exists
        chat_manager = ChatManager(self.db)
        chat = chat_manager.get_chat(chat_id)
        if not chat or chat.user_id != user_id:
            raise ValueError("Invalid chat ID for this user")

        # ✅ Update chat timestamp
        chat_manager.update_chat_timestamp(chat_id)

        # ✅ Store user message
        self.message_manager.store_message(chat_id, "user", message_text)

        # ✅ Generate title if missing
        self._generate_chat_title(chat_id, message_text)

        # ✅ Get AI response
        response_text = self.bot.chat(message_text, context={})

        # ✅ Extract structured info & update DB profile
        profile_updates = self.bot._extract_student_information(message_text)
        if profile_updates:
            self.profile_manager.update_profile(user_id, profile_updates)

        # ✅ Store bot response
        self.message_manager.store_message(chat_id, "assistant", response_text)

        # ✅ Handle recommendations - use context-aware approach
        recommendations = None
        if self._should_generate_recommendations(message_text, response_text):
            profile = self.profile_manager.get_profile(user_id)
            recommendations = self.bot.generate_personalized_recommendations(profile=profile)
            
            # Store recommendations in database
            self._store_recommendations(chat_id, recommendations)

        # ✅ Commit DB changes
        self.db.commit()

        # Format recommendations for response
        formatted_recommendations = self._format_recommendations_for_response(recommendations) if recommendations else []

        return {
            "response": response_text,
            "recommendations": formatted_recommendations
        }

    def get_recommendations(self, chat_id: str):
        """Get recommendations from database and format them properly"""
        recs = self.db.query(CollegeRecommendation).filter(
            CollegeRecommendation.chat_id == chat_id
        ).all()
        
        return self._format_recommendations_for_response(recs)