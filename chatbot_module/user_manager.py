from sqlalchemy.orm import Session
from chatbot_module.schemas import User
from datetime import datetime

class UserManager:
    """Handles user registration and retrieval"""

    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_id: str):
        """
        Registers a user with given user_id.
        Returns the User object if created or existing.
        """
        # Check if user already exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            return user, False  # User already exists

        # Create new user
        new_user = User(id=user_id, created_at=datetime.utcnow())
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user, True

    def get_user(self, user_id: str):
        """
        Fetch user by user_id.
        Returns None if not found.
        """
        return self.db.query(User).filter(User.id == user_id).first()
