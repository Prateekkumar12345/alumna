from sqlalchemy.orm import Session
from datetime import datetime
from .schemas import Message, Chat


class MessageManager:
    """Handles message storage and retrieval for chats"""

    def __init__(self, db: Session):
        self.db = db

    def store_message(self, chat_id: str, role: str, content: str):
        """
        Store a single message (user or assistant).
        """
        message = Message(
            chat_id=chat_id,
            role=role,  # 'user' or 'assistant'
            content=content,
            timestamp=datetime.utcnow()
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, chat_id: str, limit: int = 50):
        """
        Retrieve the most recent messages for a chat.
        Default limit = 50.
        """
        chat_exists = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat_exists:
            return None
        return (
            self.db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.timestamp.asc())
            .limit(limit)
            .all()
        )
