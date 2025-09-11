from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime
import uuid

from chatbot_module.schemas import Chat
from chatbot_module.config import MAX_CHATS_PER_USER

class ChatManager:
    """Handles chat sessions for users"""

    def __init__(self, db: Session):
        self.db = db

    def create_chat(self, user_id: str):
        """
        Create a new chat for a user.
        If user exceeds MAX_CHATS_PER_USER, delete the oldest chat.
        Returns the new Chat object.
        """
        # Count existing chats
        user_chats = self.db.query(Chat).filter(Chat.user_id == user_id).order_by(asc(Chat.updated_at)).all()
        if len(user_chats) >= MAX_CHATS_PER_USER:
            # Delete the oldest chat
            oldest_chat = user_chats[0]
            self.db.delete(oldest_chat)
            self.db.commit()

        # Generate unique chat ID
        chat_id = f"chat_{uuid.uuid4().hex[:12]}"

        new_chat = Chat(
            id=chat_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status="active"
        )
        self.db.add(new_chat)
        self.db.commit()
        self.db.refresh(new_chat)
        return new_chat

    def get_chats(self, user_id: str):
        """Return all active chats for a user"""
        return self.db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()

    def get_chat(self, chat_id: str):
        """Return a specific chat by chat_id"""
        return self.db.query(Chat).filter(Chat.id == chat_id).first()

    def update_chat_timestamp(self, chat_id: str):
        """Update updated_at timestamp when a chat is used"""
        chat = self.get_chat(chat_id)
        if chat:
            chat.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(chat)
        return chat
