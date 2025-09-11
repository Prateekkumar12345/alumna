from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class StudentConversation(BaseModel):
    """Simple conversation tracker without rigid field extraction"""
    conversation_id: str = Field(default_factory=lambda: f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    student_context: Dict[str, Any] = Field(default_factory=dict, description="Flexible context about the student")
    conversation_flow: List[Dict[str, str]] = Field(default_factory=list, description="Conversation history")
    insights_discovered: List[str] = Field(default_factory=list, description="Key insights about the student")
    recommendations_given: List[Dict[str, Any]] = Field(default_factory=list, description="Recommendations provided")
    conversation_stage: str = Field(default="introduction", description="Current conversation stage")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

class DynamicStudentProfile(BaseModel):
    """Dynamic student profile that can handle any fields"""
    name: Optional[str] = None
    age: Optional[int] = None
    academic_performance: Dict[str, Any] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    preferred_fields: List[str] = Field(default_factory=list)
    budget: Optional[int] = None
    location_preference: Optional[str] = None
    career_goals: List[str] = Field(default_factory=list)
    extracurricular: List[str] = Field(default_factory=list)
    family_background: Dict[str, Any] = Field(default_factory=dict)
    scores: Dict[str, Any] = Field(default_factory=dict)
    additional_info: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    message: str = Field(..., description="User's message to the counselor")
    session_id: Optional[str] = Field(None, description="Optional session ID for maintaining context")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Counselor's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    profile: Dict[str, Any] = Field(..., description="Current student profile data")
    sufficient_info: bool = Field(..., description="Whether enough info has been collected")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="College recommendations if available")

class SessionInfo(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    created_at: str = Field(..., description="Session creation timestamp")
    status: str = Field(..., description="Session status (active/completed)")
    message_count: int = Field(..., description="Number of messages in this session")

class ProfileUpdateRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to update")
    profile_data: Dict[str, Any] = Field(..., description="Profile data to update")

class RecommendationRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID (optional)")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="Custom profile data for recommendations")
    max_results: int = Field(10, description="Maximum number of recommendations to return")

class CollegeFilter(BaseModel):
    stream: Optional[str] = Field(None, description="Preferred stream/course")
    location: Optional[str] = Field(None, description="Preferred location")
    max_fees: Optional[int] = Field(None, description="Maximum fees budget")
    college_type: Optional[str] = Field(None, description="Type of college (Engineering/Medical/University/Management)")