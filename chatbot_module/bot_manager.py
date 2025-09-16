from sqlalchemy.orm import Session
from datetime import datetime
import logging

from chatbot_module.schemas import ChatRecord, Title
from chatbot_module.chat_manager import ChatManager
from chatbot_module.message_manager import MessageManager
from chatbot_module.counselor import DynamicCollegeCounselorBot
from chatbot_module.recommendation_manager import RecommendationManager
from chatbot_module.profile_manager import ProfileManager
from chatbot_module.config import OPENAI_API_KEY
from openai import OpenAI

# -------------------- OpenAI Client --------------------
client = OpenAI(api_key=OPENAI_API_KEY)


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

        try:
            # 🔥 Use correct OpenAI API call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use a valid model name
                messages=[
                    {
                        "role": "system", 
                        "content": "Generate a very short title (max 5 words) summarizing the conversation topic. Return only the title, no extra text."
                    },
                    {
                        "role": "user", 
                        "content": f"Generate a short title for this message: {first_message}"
                    }
                ],
                max_tokens=20,
                temperature=0.7
            )
            title_text = response.choices[0].message.content.strip()
            logging.info(f"Generated title: {title_text}")
            
        except Exception as e:
            logging.error(f"Error generating title with OpenAI: {e}")
            # Fallback to simple title generation
            title_text = self._generate_fallback_title(first_message)

        # ✅ Save into DB
        new_title = Title(chat_id=chat_id, title=title_text, created_at=datetime.utcnow())
        self.db.add(new_title)
        self.db.commit()
        self.db.refresh(new_title)

        return new_title.title

    def _generate_fallback_title(self, message: str) -> str:
        """Generate a fallback title when OpenAI API fails"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["recommend", "suggest", "college", "university"]):
            return "College Recommendations"
        elif any(word in message_lower for word in ["engineering", "btech", "b.tech"]):
            return "Engineering Guidance"
        elif any(word in message_lower for word in ["medical", "mbbs", "doctor"]):
            return "Medical Career Help"
        elif any(word in message_lower for word in ["mba", "business", "management"]):
            return "Business Education"
        elif any(word in message_lower for word in ["career", "job", "future"]):
            return "Career Planning"
        elif any(word in message_lower for word in ["help", "guidance", "advice"]):
            return "Educational Guidance"
        else:
            return "Chat Session"

    def _should_generate_recommendations(self, message_text: str, conversation_context: dict) -> bool:
        """Determine if recommendations should be generated based on context"""
        message_lower = message_text.lower()
        
        # Explicit recommendation requests
        if any(keyword in message_lower for keyword in ["recommend", "suggest", "college", "university", "institute"]):
            return True
        
        # Context-based triggers
        if conversation_context.get("conversation_stage") == "recommendation":
            return True
            
        if conversation_context.get("sufficient_info_collected", False):
            # Check if user is asking about options/choices
            if any(phrase in message_lower for phrase in [
                "what should i", "which one", "options", "choices", 
                "what are", "tell me about", "looking for", "need help"
            ]):
                return True
        
        # Check if user is discussing academic/career choices
        academic_keywords = ["study", "course", "degree", "program", "career", "future", "education", "btech", "engineering"]
        if any(keyword in message_lower for keyword in academic_keywords):
            return True  # Always generate recommendations for academic discussions
        
        return False

    def process_message(self, user_id: str, chat_id: str, message_text: str):
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

        # ✅ Extract structured info & update DB profile
        profile_updates = self.bot._extract_student_information(message_text)
        if profile_updates:
            self.profile_manager.update_profile(user_id, profile_updates)

        # ✅ Context-aware recommendations
        recommendations = None
        conversation_context = {
            "user_id": user_id,
            "conversation_stage": self.bot.conversation_stage,
            "sufficient_info_collected": self.bot.sufficient_info_collected,
            "message_count": self.bot.message_count
        }

        # Always try to generate recommendations for educational queries
        if self._should_generate_recommendations(message_text, conversation_context):
            logging.info("Generating recommendations based on message context")
            profile = self.profile_manager.get_profile(user_id)
            recommendations = self.bot.generate_personalized_recommendations(profile=profile)
            logging.info(f"Generated {len(recommendations) if recommendations else 0} recommendations")

            # Store recommendations in database
            if recommendations:
                for rec in recommendations:
                    new_rec = ChatRecord(
                        chat_id=chat_id,
                        recommendation_data=rec,
                        role=None,
                        content=None,
                        timestamp=datetime.utcnow()
                    )
                    self.db.add(new_rec)

        # ✅ Prepare bot input with profile context
        profile = self.profile_manager.get_profile(user_id)
        if profile:
            profile_context = (
                f"\n\n[Student Profile Context]\n"
                f"- Preferred fields: {getattr(profile, 'preferred_fields', [])}\n"
                f"- Academic scores: {getattr(profile, 'scores', {})}\n"
                f"- Career goals: {getattr(profile, 'career_goals', [])}\n"
                f"- Location preference: {getattr(profile, 'location_preference', 'Not specified')}\n"
                f"- Budget: {getattr(profile, 'budget', 'Not specified')}\n"
            )
            bot_input = message_text + profile_context
        else:
            bot_input = message_text

        # ✅ Generate bot response
        response_text = self.bot.chat(bot_input, context=conversation_context)
        self.message_manager.store_message(chat_id, "assistant", response_text)

        # ✅ Commit DB changes
        self.db.commit()

        return {
            "response": response_text,
            "recommendations": recommendations or []  # Ensure it's never None
        }

    def get_recommendations(self, chat_id: str):
        """Get all recommendations for a specific chat"""
        recs = self.db.query(ChatRecord).filter(
            ChatRecord.chat_id == chat_id,
            ChatRecord.recommendation_data.isnot(None)
        ).all()
        return [r.recommendation_data for r in recs]