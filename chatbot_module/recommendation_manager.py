from sqlalchemy.orm import Session
from datetime import datetime
from .schemas import CollegeRecommendation

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
            new_rec = CollegeRecommendation(
                chat_id=chat_id,
                recommendation_data=rec,
                created_at=datetime.utcnow()
            )
            self.db.add(new_rec)
        self.db.commit()

    def get_recommendations(self, chat_id: str):
        """
        Retrieve all stored recommendations for a chat.
        """
        recs = (
            self.db.query(CollegeRecommendation)
            .filter(CollegeRecommendation.chat_id == chat_id)
            .order_by(CollegeRecommendation.created_at.asc())
            .all()
        )
        return [r.recommendation_data for r in recs]

    def clear_recommendations(self, chat_id: str):
        """
        Delete all recommendations for a given chat.
        Useful when regenerating.
        """
        self.db.query(CollegeRecommendation).filter(
            CollegeRecommendation.chat_id == chat_id
        ).delete()
        self.db.commit()
