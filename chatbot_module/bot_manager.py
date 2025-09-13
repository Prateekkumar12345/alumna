from sqlalchemy.orm import Session
from datetime import datetime
import json
import re

from chatbot_module.schemas import CollegeRecommendation, Title
from chatbot_module.chat_manager import ChatManager
from chatbot_module.message_manager import MessageManager
from chatbot_module.recommendation.college_counselor import DynamicCollegeCounselorBot
from chatbot_module.recommendation_manager import RecommendationManager
from chatbot_module.profile_manager import ProfileManager
from chatbot_module.config import OPENAI_API_KEY
from openai import OpenAI
import logging

# -------------------- OpenAI Client --------------------
client = OpenAI(api_key=OPENAI_API_KEY)


class BotManager:
    """Manages chatbot interactions and database logging with context-aware recommendations"""

    def __init__(self, db: Session):
        self.db = db
        self.bot = DynamicCollegeCounselorBot(api_key=OPENAI_API_KEY)  # AI model
        self.message_manager = MessageManager(db)
        self.recommendation_manager = RecommendationManager(db)
        self.profile_manager = ProfileManager(db)
        
        # Context indicators for college recommendations
        self.recommendation_triggers = [
            # Direct requests
            r"recommend|suggest|advise|help.*choose|which.*college|what.*university",
            # Decision-making phrases
            r"should.*go|where.*apply|which.*program|best.*for.*me|suitable.*college",
            # Completion/graduation context
            r"after.*graduation|finished.*degree|completed.*studies|next.*step",
            # Comparison requests
            r"compare.*college|better.*university|difference.*between",
            # Career-oriented
            r"career.*college|job.*university|employment.*after|future.*prospects",
            # Application context
            r"apply.*to|application.*process|admission.*requirement|entry.*requirement",
            # Academic fit
            r"good.*fit|match.*profile|suit.*background|align.*goal",
            # Financial considerations
            r"afford.*college|scholarship.*available|financial.*aid|cost.*university",
            # Location-based
            r"college.*near|university.*in|study.*abroad|local.*institution",
            # Program-specific
            r"engineering.*college|medical.*school|business.*program|arts.*university"
        ]

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

    def _should_recommend_colleges_contextual(self, message_text: str, conversation_history: list = None) -> bool:
        """
        Determine if college recommendations should be provided based on context analysis.
        Uses both pattern matching and AI-based context understanding.
        """
        message_lower = message_text.lower()
        
        # Method 1: Enhanced pattern matching
        for pattern in self.recommendation_triggers:
            if re.search(pattern, message_lower):
                logging.info(f"Recommendation triggered by pattern: {pattern}")
                return True
        
        # Method 2: AI-based context analysis
        try:
            context_prompt = f"""
            Analyze this message in the context of college counseling and determine if the user is seeking college recommendations or guidance.
            
            Message: "{message_text}"
            
            Consider these scenarios as recommendation-worthy:
            - User is asking for college suggestions (directly or indirectly)
            - User is describing their academic profile/goals
            - User is expressing uncertainty about college choices
            - User is seeking guidance on next steps in education
            - User is comparing educational options
            - User is asking about career paths that require college education
            - User is discussing academic preferences, interests, or constraints
            
            Respond with only "YES" if recommendations are needed, "NO" if not.
            """
            
            response = client.responses.create(
                model="gpt-4",  # Using a more reliable model for this decision
                input=context_prompt,
                max_tokens=10
            )
            
            ai_decision = response.output_text.strip().upper()
            logging.info(f"AI context analysis result: {ai_decision}")
            
            if ai_decision == "YES":
                return True
                
        except Exception as e:
            logging.error(f"Error in AI context analysis: {e}")
            # Fall back to conservative approach if AI analysis fails
        
        # Method 3: Conversation history analysis (if available)
        if conversation_history:
            recent_context = " ".join([msg.get('content', '') for msg in conversation_history[-3:]])
            
            # Check if recent conversation has been about education/career planning
            education_keywords = [
                'major', 'degree', 'study', 'academic', 'gpa', 'grades', 'subject',
                'career', 'future', 'goal', 'plan', 'interest', 'passion',
                'score', 'test', 'sat', 'act', 'graduate', 'undergraduate'
            ]
            
            context_score = sum(1 for keyword in education_keywords if keyword in recent_context.lower())
            if context_score >= 2:  # At least 2 education-related keywords in recent context
                logging.info(f"Recommendation triggered by conversation context (score: {context_score})")
                return True
        
        return False

    def _analyze_recommendation_intent(self, message_text: str, user_profile: dict = None) -> dict:
        """
        Analyze the user's message to understand what kind of recommendations they need.
        Returns structured information about the recommendation request.
        """
        try:
            analysis_prompt = f"""
            Analyze this message from a student seeking college guidance and extract key information:
            
            Message: "{message_text}"
            
            Return a JSON object with these fields:
            {{
                "intent_type": "general|specific|comparison|career_focused|location_based|financial",
                "urgency": "high|medium|low",
                "specific_requirements": ["list of specific requirements mentioned"],
                "mentioned_fields": ["list of academic fields/majors mentioned"],
                "constraints": ["list of constraints like location, budget, etc."],
                "recommendation_focus": "brief description of what to focus on"
            }}
            
            If no clear college-related intent is found, return {{"intent_type": "none"}}.
            """
            
            response = client.responses.create(
                model="gpt-4",
                input=analysis_prompt,
                max_tokens=200
            )
            
            result = json.loads(response.output_text.strip())
            logging.info(f"Intent analysis result: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error in intent analysis: {e}")
            return {"intent_type": "general", "urgency": "medium"}

    def _get_conversation_history(self, chat_id: str, limit: int = 10) -> list:
        """Get recent conversation history for context analysis."""
        try:
            messages = self.message_manager.get_recent_messages(chat_id, limit)
            return [{"role": msg.role, "content": msg.content} for msg in messages]
        except Exception as e:
            logging.error(f"Error fetching conversation history: {e}")
            return []

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

        # ✅ Get conversation history for context
        conversation_history = self._get_conversation_history(chat_id)

        # ✅ Get AI response
        response_text = self.bot.chat(message_text, context={})

        # ✅ Extract structured info & update DB profile
        profile_updates = self.bot._extract_student_information(message_text)
        if profile_updates:
            self.profile_manager.update_profile(user_id, profile_updates)

        # ✅ Store bot response
        self.message_manager.store_message(chat_id, "assistant", response_text)

        # ✅ Context-aware recommendation handling
        recommendations = None
        should_recommend = self._should_recommend_colleges_contextual(
            message_text, 
            conversation_history
        )
        
        if should_recommend:
            logging.info("Context analysis indicates college recommendations needed")
            
            # Get user profile
            profile = self.profile_manager.get_profile(user_id)
            
            # Analyze the specific intent of the recommendation request
            intent_analysis = self._analyze_recommendation_intent(message_text, profile)
            
            # Generate personalized recommendations with context
            recommendations = self.bot.generate_personalized_recommendations(
                profile=profile,
                context={
                    "current_message": message_text,
                    "conversation_history": conversation_history[-5:],  # Last 5 messages
                    "intent_analysis": intent_analysis
                }
            )

            # Store recommendations in database
            if recommendations:
                for rec in recommendations:
                    new_rec = CollegeRecommendation(
                        chat_id=chat_id,
                        recommendation_data=rec,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(new_rec)
                    
                logging.info(f"Generated {len(recommendations)} recommendations based on context")

        # ✅ Commit DB changes
        self.db.commit()

        return {
            "response": response_text,
            "recommendations": recommendations,
            "context_triggered": should_recommend,
            "intent_analysis": intent_analysis if should_recommend else None
        }

    def get_recommendations(self, chat_id: str):
        """Get all recommendations for a chat session."""
        recs = self.db.query(CollegeRecommendation).filter(
            CollegeRecommendation.chat_id == chat_id
        ).all()
        return [r.recommendation_data for r in recs]

    def get_contextual_recommendations(self, user_id: str, chat_id: str, context_filter: str = None):
        """
        Get recommendations filtered by context or intent type.
        """
        profile = self.profile_manager.get_profile(user_id)
        conversation_history = self._get_conversation_history(chat_id)
        
        # Generate fresh recommendations based on current context
        recommendations = self.bot.generate_personalized_recommendations(
            profile=profile,
            context={
                "conversation_history": conversation_history,
                "filter": context_filter
            }
        )
        
        return recommendations