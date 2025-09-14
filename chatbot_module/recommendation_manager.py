from sqlalchemy.orm import Session
from datetime import datetime
from .schemas import ChatRecord


class RecommendationManager:
    """Handles storing and retrieving college recommendations"""

    def __init__(self, db: Session):
        self.db = db

    def store_recommendations(self, chat_id: str, recommendations: list):
        """
        Store multiple recommendations for a given chat.
        Each recommendation is expected to be a dict.
        """
        for rec in recommendations:
            record = ChatRecord(
                chat_id=chat_id,
                role=None,  # Not a chat message
                content=None,
                recommendation_data=rec,
                timestamp=datetime.utcnow()
            )
            self.db.add(record)
        self.db.commit()

    def get_recommendations(self, chat_id: str):
        """
        Retrieve all stored recommendations for a chat.
        """
        recs = (
            self.db.query(ChatRecord)
            .filter(ChatRecord.chat_id == chat_id, ChatRecord.recommendation_data.isnot(None))
            .order_by(ChatRecord.timestamp.asc())
            .all()
        )
        return [r.recommendation_data for r in recs]

    def clear_recommendations(self, chat_id: str):
        """
        Delete all recommendations for a given chat.
        """
        self.db.query(ChatRecord).filter(
            ChatRecord.chat_id == chat_id,
            ChatRecord.recommendation_data.isnot(None)
        ).delete()
        self.db.commit()
