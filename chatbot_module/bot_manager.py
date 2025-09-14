from sqlalchemy.orm import Session
from datetime import datetime

from chatbot_module.schemas import CollegeRecommendation, Title
from chatbot_module.chat_manager import ChatManager
from chatbot_module.message_manager import MessageManager
from chatbot_module.counselor import DynamicCollegeCounselorBot
from chatbot_module.recommendation_manager import RecommendationManager
from chatbot_module.profile_manager import ProfileManager
from chatbot_module.config import OPENAI_API_KEY
from openai import OpenAI
import logging

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

        # 🔥 Use OpenAI to generate title
        response = client.responses.create(
            model="gpt-5",
            input=f"Generate a very short title (max 5 words) summarizing this conversation topic:\n\n{first_message}"
        )
        title_text = response.output_text.strip()
        logging.info(f"Title : {title_text}")

        # ✅ Save into DB
        new_title = Title(chat_id=chat_id, title=title_text, created_at=datetime.utcnow())
        self.db.add(new_title)
        self.db.commit()
        self.db.refresh(new_title)

        return new_title.title

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

        # ✅ Handle recommendations
        recommendations = None
        if "college" in message_text.lower() or "recommend" in message_text.lower():
            profile = self.profile_manager.get_profile(user_id)
            recommendations = self.bot.generate_personalized_recommendations(profile=profile)

            for rec in recommendations:
                new_rec = CollegeRecommendation(
                    chat_id=chat_id,
                    recommendation_data=rec,
                    created_at=datetime.utcnow()
                )
                self.db.add(new_rec)

        # ✅ Commit DB changes
        self.db.commit()

        return {
            "response": response_text,
            "recommendations": recommendations
        }

    def get_recommendations(self, chat_id: str):
        recs = self.db.query(CollegeRecommendation).filter(
            CollegeRecommendation.chat_id == chat_id
        ).all()
        return [r.recommendation_data for r in recs]
