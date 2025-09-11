from sqlalchemy.orm import Session
from chatbot_module.schemas import StudentProfile
from datetime import datetime

class ProfileManager:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user_id: str) -> StudentProfile:
        profile = self.db.query(StudentProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = StudentProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_profile(self, user_id: str, updates: dict) -> StudentProfile:
        profile = self.get_profile(user_id)
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
            else:
                # Store in JSON additional_info
                profile.additional_info[key] = value
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile
