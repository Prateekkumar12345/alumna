from sqlalchemy.orm import Session
from datetime import datetime
from .schemas import Chat, ChatRecord


class MessageManager:
    """Handles message storage and retrieval for chats"""

    def __init__(self, db: Session):
        self.db = db

    def store_message(self, chat_id: str, role: str, content: str):
        """
        Store a single message (user or assistant).
        """
        record = ChatRecord(
            chat_id=chat_id,
            role=role,  # 'user' or 'assistant'
            content=content,
            timestamp=datetime.utcnow(),
            recommendation_data=None  # Explicitly mark as message
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_messages(self, chat_id: str, limit: int = 50):
        """
        Retrieve the most recent chat messages (not recommendations) for a chat.
        """
        chat_exists = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat_exists:
            return None

        return (
            self.db.query(ChatRecord)
            .filter(ChatRecord.chat_id == chat_id, ChatRecord.role.isnot(None))
            .order_by(ChatRecord.timestamp.asc())
            .limit(limit)
            .all()
        )
