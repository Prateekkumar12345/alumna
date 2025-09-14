# Enhanced bot_manager.py
from sqlalchemy.orm import Session
from datetime import datetime
import re
import logging
from typing import Dict, Any, List

from chatbot_module.schemas import CollegeRecommendation, Title
from chatbot_module.chat_manager import ChatManager
from chatbot_module.message_manager import MessageManager
from chatbot_module.counselor import DynamicCollegeCounselorBot
from chatbot_module.recommendation_manager import RecommendationManager
from chatbot_module.profile_manager import ProfileManager
from chatbot_module.config import OPENAI_API_KEY
from openai import OpenAI

# -------------------- OpenAI Client --------------------
client = OpenAI(api_key=OPENAI_API_KEY)


class ContextAnalyzer:
    """Analyzes conversation context to determine when recommendations should be provided"""
    
    def __init__(self):
        # Intent patterns for recommendation triggers
        self.recommendation_intents = {
            'direct_request': [
                r'\b(?:suggest|recommend|tell me about|show me|list|find me|help me find)\b.*\b(?:college|university|institute|school)\b',
                r'\b(?:college|university|institute)\b.*\b(?:suggest|recommend|for me|options)\b',
                r'\b(?:which|what)\b.*\b(?:college|university|institute)\b.*\b(?:should|good|best|suitable)\b',
                r'\b(?:where|which place)\b.*\b(?:study|education|admission)\b'
            ],
            'exploration': [
                r'\b(?:exploring|looking for|searching for|considering)\b.*\b(?:college|university|options|courses)\b',
                r'\b(?:career|future|next step|after)\b.*\b(?:college|university|study|education)\b',
                r'\b(?:confused|unsure|help)\b.*\b(?:college|career|study|course)\b',
                r'\bi want to\b.*\b(?:study|pursue|learn|do|become)\b'
            ],
            'comparison': [
                r'\b(?:compare|difference|better|vs|versus)\b.*\b(?:college|university|course)\b',
                r'\b(?:college|university)\b.*\b(?:comparison|compare|choice)\b'
            ],
            'information_seeking': [
                r'\b(?:tell me about|information about|details about|know about)\b.*\b(?:college|university|course|field)\b',
                r'\b(?:admission|entrance|eligibility|fee|cost|scholarship)\b.*\b(?:college|university)\b',
                r'\b(?:college|university)\b.*\b(?:admission|entrance|eligibility|fee|cost|scholarship)\b'
            ],
            'decision_making': [
                r'\b(?:should i|can i|is it good|worth|right choice)\b.*\b(?:college|university|course|field)\b',
                r'\b(?:final|decide|decision|choose|select)\b.*\b(?:college|university|course)\b'
            ]
        }
        
        # Context indicators that suggest student is ready for recommendations
        self.readiness_indicators = [
            r'\b(?:ready|prepared|decided|clear|sure)\b.*\b(?:about|for|on)\b',
            r'\b(?:enough|sufficient)\b.*\b(?:information|details|data)\b',
            r'\b(?:narrowed down|shortlist|final|conclude)\b',
            r'\b(?:next step|move forward|proceed)\b'
        ]
        
        # Profile completeness indicators
        self.profile_indicators = {
            'interests': [r'\b(?:interested in|like|enjoy|passionate about|love)\b', 
                         r'\b(?:computer|technology|medical|business|arts|science|engineering)\b'],
            'academic': [r'\b(?:\d+\s*%|percent|grade|score|marks|cgpa|gpa)\b',
                        r'\b(?:good|excellent|average|poor)\b.*\b(?:student|performance|grades)\b'],
            'location': [r'\b(?:from|in|near|around|prefer|want to stay)\b.*\b(?:delhi|mumbai|bangalore|pune|hyderabad|chennai|kolkata|city)\b'],
            'budget': [r'\b(?:\d+\s*(?:lakh|thousand|crore|rupees|₹))\b',
                      r'\b(?:budget|afford|cost|expensive|cheap|money)\b']
        }

    def analyze_context(self, message: str, conversation_history: List[Dict], student_profile: Any) -> Dict[str, Any]:
        """Analyze message and conversation context to determine recommendation readiness"""
        message_lower = message.lower()
        
        analysis = {
            'should_recommend': False,
            'recommendation_type': None,
            'confidence_score': 0.0,
            'context_signals': [],
            'profile_completeness': 0.0,
            'conversation_stage': self._determine_stage(conversation_history, student_profile)
        }
        
        # Check for direct recommendation intents
        intent_scores = {}
        for intent_type, patterns in self.recommendation_intents.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
                    analysis['context_signals'].append(f"Direct {intent_type} detected")
            
            if score > 0:
                intent_scores[intent_type] = score / len(patterns)
        
        # Calculate profile completeness
        analysis['profile_completeness'] = self._calculate_profile_completeness(student_profile)
        
        # Determine if recommendations should be provided
        if intent_scores:
            # Direct intent detected
            analysis['should_recommend'] = True
            analysis['recommendation_type'] = max(intent_scores, key=intent_scores.get)
            analysis['confidence_score'] = max(intent_scores.values())
            
        elif analysis['profile_completeness'] > 0.6:
            # Sufficient profile information available
            readiness_score = self._check_readiness_indicators(message_lower)
            if readiness_score > 0.3 or analysis['conversation_stage'] in ['detailed_guidance', 'recommendation']:
                analysis['should_recommend'] = True
                analysis['recommendation_type'] = 'contextual'
                analysis['confidence_score'] = readiness_score
                analysis['context_signals'].append("High profile completeness + contextual readiness")
        
        # Boost confidence based on conversation stage and message count
        if len(conversation_history) >= 4 and analysis['conversation_stage'] in ['detailed_guidance', 'recommendation']:
            analysis['confidence_score'] += 0.2
            analysis['context_signals'].append("Extended conversation detected")
        
        # Check for implicit recommendation scenarios
        implicit_score = self._check_implicit_scenarios(message_lower, conversation_history)
        if implicit_score > 0.5:
            analysis['should_recommend'] = True
            analysis['recommendation_type'] = 'implicit'
            analysis['confidence_score'] = max(analysis['confidence_score'], implicit_score)
            analysis['context_signals'].append("Implicit recommendation scenario detected")
        
        return analysis

    def _determine_stage(self, conversation_history: List[Dict], student_profile: Any) -> str:
        """Determine current conversation stage"""
        message_count = len(conversation_history)
        
        if message_count <= 2:
            return "greeting"
        elif message_count <= 4:
            return "information_gathering"
        elif self._calculate_profile_completeness(student_profile) > 0.6:
            return "recommendation"
        elif message_count > 6:
            return "detailed_guidance"
        else:
            return "information_gathering"

    def _calculate_profile_completeness(self, student_profile: Any) -> float:
        """Calculate how complete the student profile is"""
        if not student_profile:
            return 0.0
        
        completeness_score = 0.0
        total_weight = 5.0
        
        # Check key profile attributes
        if hasattr(student_profile, 'preferred_fields') and student_profile.preferred_fields:
            completeness_score += 1.5
        
        if hasattr(student_profile, 'academic_performance') and student_profile.academic_performance:
            completeness_score += 1.0
        
        if hasattr(student_profile, 'location_preference') and student_profile.location_preference:
            completeness_score += 1.0
        
        if hasattr(student_profile, 'budget') and student_profile.budget:
            completeness_score += 1.0
        
        if hasattr(student_profile, 'interests') and student_profile.interests:
            completeness_score += 0.5
        
        return min(completeness_score / total_weight, 1.0)

    def _check_readiness_indicators(self, message_lower: str) -> float:
        """Check for indicators that student is ready for recommendations"""
        score = 0.0
        total_indicators = len(self.readiness_indicators)
        
        for pattern in self.readiness_indicators:
            if re.search(pattern, message_lower):
                score += 1.0
        
        return score / total_indicators if total_indicators > 0 else 0.0

    def _check_implicit_scenarios(self, message_lower: str, conversation_history: List[Dict]) -> float:
        """Check for implicit scenarios that suggest need for recommendations"""
        score = 0.0
        
        # Scenario 1: Student mentions completing education or exams
        completion_patterns = [
            r'\b(?:completed|finished|done with|cleared)\b.*\b(?:12th|graduation|exam|test)\b',
            r'\b(?:results|scores|marks)\b.*\b(?:declared|announced|got|received)\b'
        ]
        for pattern in completion_patterns:
            if re.search(pattern, message_lower):
                score += 0.3
                break
        
        # Scenario 2: Future planning context
        planning_patterns = [
            r'\b(?:next year|coming year|planning|thinking about|considering)\b.*\b(?:study|education|admission)\b',
            r'\b(?:after|post)\b.*\b(?:12th|graduation|exam)\b'
        ]
        for pattern in planning_patterns:
            if re.search(pattern, message_lower):
                score += 0.4
                break
        
        # Scenario 3: Uncertainty or confusion about choices
        confusion_patterns = [
            r'\b(?:confused|uncertain|not sure|don\'t know|help me)\b.*\b(?:what to do|which|where|how)\b',
            r'\b(?:many options|so many|overwhelmed|difficult to choose)\b'
        ]
        for pattern in confusion_patterns:
            if re.search(pattern, message_lower):
                score += 0.5
                break
        
        # Scenario 4: Repeated mentions of education/career topics
        if len(conversation_history) >= 3:
            education_mentions = 0
            for msg in conversation_history[-3:]:
                content = msg.get('content', '').lower()
                if any(word in content for word in ['college', 'university', 'course', 'study', 'career', 'education']):
                    education_mentions += 1
            
            if education_mentions >= 2:
                score += 0.3
        
        return score


class BotManager:
    """Enhanced chatbot manager with context-aware recommendations"""

    def __init__(self, db: Session):
        self.db = db
        self.bot = DynamicCollegeCounselorBot(api_key=OPENAI_API_KEY)
        self.message_manager = MessageManager(db)
        self.recommendation_manager = RecommendationManager(db)
        self.profile_manager = ProfileManager(db)
        self.context_analyzer = ContextAnalyzer()

    def _generate_chat_title(self, chat_id: str, first_message: str) -> str:
        """Generate a title for the chat using OpenAI and store it if not exists."""
        existing_title = self.db.query(Title).filter(Title.chat_id == chat_id).first()
        if existing_title:
            return existing_title.title

        try:
            # Fixed OpenAI API call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate a very short title (max 5 words) summarizing the conversation topic."},
                    {"role": "user", "content": first_message}
                ],
                max_tokens=50,
                temperature=0.7
            )
            title_text = response.choices[0].message.content.strip()
            logging.info(f"Generated title: {title_text}")
        except Exception as e:
            logging.error(f"Error generating title: {e}")
            title_text = "College Counseling Chat"

        # Save into DB
        new_title = Title(chat_id=chat_id, title=title_text, created_at=datetime.utcnow())
        self.db.add(new_title)
        self.db.commit()
        self.db.refresh(new_title)

        return new_title.title

    def process_message(self, user_id: str, chat_id: str, message_text: str):
        """Enhanced message processing with context-aware recommendations"""
        # Validate chat exists
        chat_manager = ChatManager(self.db)
        chat = chat_manager.get_chat(chat_id)
        if not chat or chat.user_id != user_id:
            raise ValueError("Invalid chat ID for this user")

        # Update chat timestamp
        chat_manager.update_chat_timestamp(chat_id)

        # Get conversation history for context analysis
        conversation_history = self.message_manager.get_chat_messages(chat_id)
        
        # Store user message
        self.message_manager.store_message(chat_id, "user", message_text)

        # Generate title if missing
        self._generate_chat_title(chat_id, message_text)

        # Extract structured info & update DB profile BEFORE context analysis
        profile_updates = self.bot._extract_student_information(message_text)
        if profile_updates:
            self.profile_manager.update_profile(user_id, profile_updates)

        # Get updated profile for context analysis
        updated_profile = self.profile_manager.get_profile(user_id)
        
        # Analyze conversation context
        context_analysis = self.context_analyzer.analyze_context(
            message_text, 
            conversation_history, 
            updated_profile
        )

        # Log context analysis for debugging
        logging.info(f"Context Analysis: {context_analysis}")

        # Get AI response with context
        response_text = self.bot.chat(message_text, context={
            'analysis': context_analysis,
            'conversation_history': conversation_history,
            'profile': updated_profile
        })

        # Store bot response
        self.message_manager.store_message(chat_id, "assistant", response_text)

        # Handle context-aware recommendations
        recommendations = None
        if context_analysis['should_recommend'] and context_analysis['confidence_score'] > 0.3:
            logging.info(f"Generating recommendations based on context: {context_analysis['recommendation_type']}")
            
            try:
                recommendations = self.bot.generate_personalized_recommendations(profile=updated_profile)
                
                if recommendations:
                    # Store recommendations in database
                    for rec in recommendations[:5]:  # Limit to top 5 recommendations
                        new_rec = CollegeRecommendation(
                            chat_id=chat_id,
                            recommendation_data={
                                **rec,
                                'context_type': context_analysis['recommendation_type'],
                                'confidence_score': context_analysis['confidence_score'],
                                'generated_at': datetime.utcnow().isoformat()
                            },
                            created_at=datetime.utcnow()
                        )
                        self.db.add(new_rec)
                    
                    logging.info(f"Generated {len(recommendations)} recommendations")
                else:
                    logging.warning("No recommendations generated despite context indicating need")
                    
            except Exception as e:
                logging.error(f"Error generating recommendations: {e}")

        # Commit DB changes
        self.db.commit()

        return {
            "response": response_text,
            "recommendations": recommendations,
            "context_analysis": context_analysis,  # Include for debugging/frontend use
            "profile_completeness": context_analysis['profile_completeness']
        }

    def get_recommendations(self, chat_id: str):
        """Get all recommendations for a chat"""
        recs = self.db.query(CollegeRecommendation).filter(
            CollegeRecommendation.chat_id == chat_id
        ).order_by(CollegeRecommendation.created_at.desc()).all()
        return [r.recommendation_data for r in recs]

    def get_context_insights(self, chat_id: str):
        """Get context insights for a conversation"""
        messages = self.message_manager.get_chat_messages(chat_id)
        if not messages:
            return {"stage": "greeting", "completeness": 0.0}
        
        # Get user for profile
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return {"stage": "greeting", "completeness": 0.0}
            
        profile = self.profile_manager.get_profile(chat.user_id)
        latest_message = messages[-1]['content'] if messages else ""
        
        analysis = self.context_analyzer.analyze_context(latest_message, messages, profile)
        
        return {
            "stage": analysis['conversation_stage'],
            "completeness": analysis['profile_completeness'],
            "signals": analysis['context_signals'],
            "ready_for_recommendations": analysis['should_recommend']
        }


# Enhanced counselor.py additions
class EnhancedDynamicCollegeCounselorBot(DynamicCollegeCounselorBot):
    """Enhanced counselor with better context awareness"""
    
    def chat(self, message, context):
        """Enhanced chat function with context awareness"""
        self.message_count += 1
        
        # Extract context information
        analysis = context.get('analysis', {})
        conversation_history = context.get('conversation_history', [])
        profile = context.get('profile')
        
        # Update conversation stage based on context analysis
        if analysis.get('conversation_stage'):
            self.conversation_stage = analysis['conversation_stage']
        else:
            self._update_conversation_stage(message)
        
        # Extract and store student information
        self._extract_student_information(message)
        
        # Add to extraction history with context
        self.extraction_history.append({
            "message": message,
            "stage": self.conversation_stage,
            "context_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if self.use_openai:
            try:
                # Enhanced system prompt with context
                system_prompt = self._get_context_aware_system_prompt(analysis, profile)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                
                # Add recent conversation context
                recent_history = self.conversation_history[-8:]
                for i in range(0, len(recent_history)-1, 2):
                    if i+1 < len(recent_history):
                        messages.insert(-1, {"role": "user", "content": recent_history[i]["content"]})
                        messages.insert(-1, {"role": "assistant", "content": recent_history[i+1]["content"]})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000,
                    frequency_penalty=0.3,
                    presence_penalty=0.2
                )
                
                assistant_response = response.choices[0].message.content
                
            except Exception as e:
                logging.error(f"OpenAI API error: {e}")
                assistant_response = self._get_enhanced_fallback_response(message, analysis, profile)
        else:
            assistant_response = self._get_enhanced_fallback_response(message, analysis, profile)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return assistant_response

    def _get_context_aware_system_prompt(self, analysis, profile):
        """Generate context-aware system prompt"""
        base_prompt = self._get_dynamic_system_prompt()
        
        context_additions = []
        
        if analysis.get('should_recommend'):
            context_additions.append(f"""
CONTEXT ALERT: The student's message indicates they are ready for college recommendations.
Recommendation Type: {analysis.get('recommendation_type', 'general')}
Confidence: {analysis.get('confidence_score', 0):.2f}
Signals: {', '.join(analysis.get('context_signals', []))}

Based on this context, you should:
1. Acknowledge their readiness for specific guidance
2. Provide targeted recommendations if you have enough profile information
3. Ask clarifying questions if profile is incomplete
4. Be more directive and specific in your advice
""")

        if profile and hasattr(profile, 'preferred_fields') and profile.preferred_fields:
            context_additions.append(f"""
STUDENT PROFILE CONTEXT:
- Interested Fields: {', '.join(profile.preferred_fields)}
- Profile Completeness: {analysis.get('profile_completeness', 0):.1%}
- Conversation Stage: {analysis.get('conversation_stage', 'unknown')}

Tailor your response to their specific interests and provide relevant insights.
""")

        if analysis.get('conversation_stage') == 'recommendation':
            context_additions.append("""
RECOMMENDATION STAGE: Focus on providing specific, actionable college and career guidance.
Be detailed, practical, and include next steps they should take.
""")

        return base_prompt + "\n".join(context_additions)

    def _get_enhanced_fallback_response(self, message, analysis, profile):
        """Enhanced fallback response with context awareness"""
        message_lower = message.lower()
        
        # Context-aware responses based on analysis
        if analysis.get('should_recommend') and analysis.get('confidence_score', 0) > 0.5:
            return self._get_recommendation_focused_response(message_lower, profile)
        
        if analysis.get('conversation_stage') == 'information_gathering':
            return self._get_information_gathering_response(message_lower, profile)
        
        # Default to original fallback
        return self._get_fallback_response(message)

    def _get_recommendation_focused_response(self, message_lower, profile):
        """Generate response focused on providing recommendations"""
        if hasattr(profile, 'preferred_fields') and profile.preferred_fields:
            fields = ', '.join(profile.preferred_fields)
            return f"""Great! I can see you're interested in {fields} and ready to explore specific college options. Let me provide you with some targeted recommendations based on your profile.

Here are some key considerations for your field(s):

🎯 **Top College Categories:**
- Premier institutes with excellent placement records
- Specialized colleges focusing on {fields}
- Emerging institutes with modern curriculum

📍 **Location Factors:**
- Industry hubs offer better internship opportunities
- Consider living costs and family proximity
- Campus infrastructure and research facilities

💼 **Career Prospects:**
- Current industry trends and demand
- Starting salaries and growth potential
- Skill development opportunities

Would you like me to suggest specific colleges based on your preferences? Also, do you have any location preferences or budget constraints I should consider?"""
        
        return """I can sense you're ready to explore specific college options! To provide you with the most relevant recommendations, let me understand your preferences better:

🎓 **Academic Interests**: Which fields or subjects excite you most?
📍 **Location**: Any preferred cities or regions?
💰 **Budget**: What's your expected investment range?
🏆 **Goals**: Career aspirations or specific outcomes you're looking for?

Once I understand these aspects, I can provide you with highly personalized college recommendations that match your profile perfectly!"""

    def _get_information_gathering_response(self, message_lower, profile):
        """Generate response focused on gathering more profile information"""
        missing_info = []
        
        if not hasattr(profile, 'preferred_fields') or not profile.preferred_fields:
            missing_info.append("academic interests")
        
        if not hasattr(profile, 'location_preference') or not profile.location_preference:
            missing_info.append("location preference")
            
        if not hasattr(profile, 'budget') or not profile.budget:
            missing_info.append("budget range")

        if missing_info:
            return f"""Thank you for sharing that! I'm building a comprehensive profile to provide you with the best guidance. 

To give you more personalized recommendations, I'd love to learn about your {', '.join(missing_info[:2])}.

For example:
- What subjects or career fields interest you most?
- Do you have any preferred locations for studying?
- Any specific goals or outcomes you're hoping to achieve?

The more I understand about your aspirations and constraints, the better I can guide you toward the right educational path!"""
        
        return """Perfect! I'm getting a good sense of your profile. Based on what you've shared, I can start providing more specific guidance. What particular aspect would you like to dive deeper into - specific colleges, career prospects, or admission strategies?"""