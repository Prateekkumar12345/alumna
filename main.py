# from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Query, Body
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from sqlalchemy.orm import Session
# import tempfile
# import os
# import sys
# from chatbot_module.database import get_db
# from chatbot_module.user_manager import UserManager
# from chatbot_module.chat_manager import ChatManager
# from chatbot_module.bot_manager import BotManager
# from chatbot_module.message_manager import MessageManager
# from chatbot_module.recommendation_manager import RecommendationManager
# from resume_analyzer.ai_analyzer import AIResumeAnalyzer
# from resume_analyzer.resume_parser import ResumeParser
# from resume_analyzer.scoring_engine import ATSScoringEngine
# from resume_analyzer.strength_weakness_analyzer import StrengthWeaknessAnalyzer
# from resume_analyzer.job_matcher import JobRoleMatcher
# from resume_analyzer.pdf_extractor import PDFExtractor
# from resume_analyzer.config import ATS_KEYWORDS, INDUSTRY_INSIGHTS

# from chatbot_module.schemas import  Title, ChatRecord

# app = FastAPI(title="Chatbot Module API")

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure appropriately for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app = FastAPI(title="Chatbot Module API")

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure appropriately for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize resume analyzer components
# pdf_extractor = PDFExtractor()
# resume_parser = ResumeParser()
# scoring_engine = ATSScoringEngine()
# strength_weakness_analyzer = StrengthWeaknessAnalyzer()
# job_matcher = JobRoleMatcher()
# ai_analyzer = AIResumeAnalyzer()

# # Helper functions for resume analysis
# def generate_executive_summary(sections, total_score, max_score, score_breakdown):
#     """Generate executive summary from analysis results"""
#     score_percentage = (total_score / max_score) * 100
#     overall_assessment = score_breakdown.get('overall_assessment', {})
    
#     return {
#         "professional_profile": {
#             "experience_level": sections.get('experience_level', 'Not determined'),
#             "technical_skills_count": sections.get('skills_count', 0),
#             "project_portfolio_size": sections.get('project_count', 0),
#             "achievement_metrics": sections.get('quantified_achievements', 0),
#             "technical_sophistication": sections.get('technical_sophistication', 'Basic')
#         },
#         "contact_presentation": {
#             "email_address": "Present" if sections.get('email') else "Missing",
#             "phone_number": "Present" if sections.get('phone') else "Missing",
#             "education": "Documented" if sections.get('has_education') else "Missing",
#             "resume_length": sections.get('word_count', 0),
#             "action_verbs": sections.get('action_verb_count', 0)
#         },
#         "overall_assessment": {
#             "score_percentage": score_percentage,
#             "level": overall_assessment.get('level', 'Unknown'),
#             "description": overall_assessment.get('description', ''),
#             "recommendation": overall_assessment.get('recommendation', '')
#         }
#     }

# def generate_detailed_scoring(score_breakdown):
#     """Generate detailed scoring breakdown"""
#     detailed_scores = {}
    
#     for category, data in score_breakdown.items():
#         if category == 'overall_assessment':
#             continue
            
#         category_name = category.replace('_', ' ').title()
#         percentage = (data['score'] / data['max']) * 100
        
#         detailed_scores[category] = {
#             "score": data['score'],
#             "max_score": data['max'],
#             "percentage": percentage,
#             "details": data.get('details', [])
#         }
    
#     return detailed_scores

# def generate_improvement_plan(weaknesses_detailed):
#     """Generate improvement plan from weaknesses"""
#     # Group recommendations by priority
#     critical_fixes = [w for w in weaknesses_detailed if w.get('fix_priority', '').startswith('CRITICAL')]
#     high_priority = [w for w in weaknesses_detailed if w.get('fix_priority', '').startswith('HIGH')]
#     medium_priority = [w for w in weaknesses_detailed if w.get('fix_priority', '').startswith('MEDIUM')]
    
#     return {
#         "critical_fixes": critical_fixes,
#         "high_priority_improvements": high_priority,
#         "medium_priority_enhancements": medium_priority,
#         "implementation_timeline": [
#             {"period": "Week 1-2", "task": "Fix critical contact and formatting issues", "priority": "🔴"},
#             {"period": "Month 1-2", "task": "Enhance content quality and technical depth", "priority": "🟡"},
#             {"period": "Month 2-3", "task": "Build project portfolio and quantified achievements", "priority": "🟠"},
#             {"period": "Month 3-6", "task": "Advanced skill development and specialization", "priority": "🟢"}
#         ]
#     }

# # Resume Analyzer Endpoints
# @app.post("/analyze-resume")
# async def analyze_resume(
#     file: UploadFile = File(...), 
#     target_role: str = None,
#     api_key: str = None
# ):
#     """
#     Main endpoint to analyze a resume PDF and return comprehensive results
#     """
#     try:
#         # Validate file type
#         if file.content_type != "application/pdf":
#             raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
#         # Set API key if provided
#         if api_key:
#             ai_analyzer.set_api_key(api_key)
        
#         # Save uploaded file temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             content = await file.read()
#             tmp_file.write(content)
#             tmp_file_path = tmp_file.name
        
#         try:
#             # Extract text from PDF
#             resume_text = pdf_extractor.extract_text_from_pdf_path(tmp_file_path)
            
#             if not resume_text:
#                 raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
            
#             # Validate resume content
#             is_valid, validation_message = pdf_extractor.validate_resume_content(resume_text)
#             if not is_valid:
#                 return JSONResponse(
#                     status_code=400,
#                     content={"error": "Invalid resume content", "details": validation_message}
#                 )
            
#             # Parse resume sections
#             sections = resume_parser.extract_comprehensive_sections(resume_text)
            
#             # Get AI analysis if API key is provided
#             ai_comprehensive = None
#             ai_targeted = None
            
#             if api_key:
#                 try:
#                     ai_comprehensive = ai_analyzer.get_comprehensive_ai_analysis(resume_text, target_role)
#                     if target_role:
#                         ai_targeted = ai_analyzer.get_targeted_role_analysis(resume_text, target_role)
#                 except Exception as e:
#                     print(f"AI analysis error: {e}")
            
#             # Calculate scores
#             total_score, max_score, score_breakdown = scoring_engine.calculate_comprehensive_ats_score(
#                 resume_text, sections, target_role
#             )
            
#             # Get strengths and weaknesses
#             strengths_detailed, weaknesses_detailed = strength_weakness_analyzer.analyze_comprehensive_strengths_weaknesses(
#                 resume_text, sections, target_role
#             )
            
#             # Get job market analysis
#             job_analysis = job_matcher.get_comprehensive_job_analysis(resume_text, sections, target_role)
            
#             # Prepare response
#             response_data = {
#                 "success": True,
#                 "resume_metadata": {
#                     "word_count": sections.get('word_count', 0),
#                     "validation_message": validation_message,
#                     "experience_level": sections.get('experience_level', 'Not determined'),
#                     "skills_count": sections.get('skills_count', 0),
#                     "project_count": sections.get('project_count', 0)
#                 },
#                 "executive_summary": generate_executive_summary(sections, total_score, max_score, score_breakdown),
#                 "detailed_scoring": generate_detailed_scoring(score_breakdown),
#                 "strengths_analysis": strengths_detailed,
#                 "weaknesses_analysis": weaknesses_detailed,
#                 "improvement_plan": generate_improvement_plan(weaknesses_detailed),
#                 "job_market_analysis": job_analysis,
#                 "ai_analysis": {
#                     "comprehensive": ai_comprehensive,
#                     "targeted": ai_targeted
#                 } if api_key else {"message": "API key required for AI analysis"}
#             }
            
#             return response_data
            
#         finally:
#             # Clean up temporary file
#             os.unlink(tmp_file_path)
            
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# @app.post("/test-pdf-extraction")
# async def test_pdf_extraction(file: UploadFile = File(...)):
#     """
#     Test endpoint to verify PDF extraction is working
#     """
#     try:
#         # Validate file type
#         if file.content_type != "application/pdf":
#             raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
#         # Save uploaded file temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             content = await file.read()
#             tmp_file.write(content)
#             tmp_file_path = tmp_file.name
        
#         try:
#             # Extract text from PDF
#             resume_text = pdf_extractor.extract_text_from_pdf_path(tmp_file_path)
            
#             if not resume_text:
#                 raise HTTPException(
#                     status_code=400, 
#                     detail="Failed to extract text from PDF"
#                 )
            
#             # Validate resume content
#             is_valid, validation_message = pdf_extractor.validate_resume_content(resume_text)
            
#             return {
#                 "success": True,
#                 "extracted_text_length": len(resume_text),
#                 "word_count": len(resume_text.split()),
#                 "is_valid_resume": is_valid,
#                 "validation_message": validation_message,
#                 "text_preview": resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text
#             }
            
#         finally:
#             # Clean up temporary file
#             os.unlink(tmp_file_path)
            
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"PDF extraction test failed: {str(e)}")




# # -------------------- Chat Creation --------------------
# @app.post("/chat/create")
# def create_chat(user_id: str = Query(..., description="User ID"), db: Session = Depends(get_db)):
#     user_manager = UserManager(db)
#     chat_manager = ChatManager(db)

#     # ✅ Auto-register user if not exists
#     user, created = user_manager.register_user(user_id)

#     # ✅ Create chat
#     chat = chat_manager.create_chat(user_id)
#     return {
#         "user_id": user.id,
#         "chat_id": chat.id,
#         "created_at": chat.created_at,
#         "message": "User created and chat started" if created else "Chat started"
#     }

# # -------------------- List User Chats --------------------
# @app.get("/chat/list")
# def list_chats(user_id: str = Query(..., description="User ID"), db: Session = Depends(get_db)):
#     user_manager = UserManager(db)
#     user = user_manager.get_user(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     chat_manager = ChatManager(db)
#     chats = chat_manager.get_chats(user_id)

#     return [
#         {
#             "chat_id": c.id,
#             "title": c.title.title if c.title else "Untitled Chat",  # ✅ Add chat title
#             "created_at": c.created_at,
#             "updated_at": c.updated_at,
#             "status": c.status
#         }
#         for c in chats
#     ]


# # -------------------- Send Message --------------------
# @app.post("/chat/send")
# def send_message(
#     user_id: str = Query(..., description="User ID"),
#     chat_id: str = Query(..., description="Chat ID"),
#     message: str = Body(..., embed=True, description="User message"),
#     db: Session = Depends(get_db)
# ):
#     user_manager = UserManager(db)
#     user = user_manager.get_user(user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     bot_manager = BotManager(db)
#     try:
#         result = bot_manager.process_message(user_id, chat_id, message)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     if result["recommendations"] is None:
#         result["recommendations"] = []

#     # ✅ Fetch chat title
#     title_obj = db.query(Title).filter(Title.chat_id == chat_id).first()
#     chat_title = title_obj.title if title_obj else "Untitled Chat"

#     return {
#         "chat_id": chat_id,
#         "title": chat_title,
#         "user_message": message,
#         "bot_response": result["response"],
#         "recommendations": result["recommendations"]
#     }




# @app.get("/chat/messages")
# def get_chat_messages(
#     chat_id: str = Query(..., description="Chat ID"),
#     db: Session = Depends(get_db)
# ):
#     # ✅ Fetch all chat records (both messages & recommendations)
#     records = db.query(ChatRecord).filter(ChatRecord.chat_id == chat_id).all()
#     if not records:
#         raise HTTPException(
#             status_code=404,
#             detail={
#                 "error": True,
#                 "chat_id": chat_id,
#                 "title": "",
#                 "messages": [],
#                 "recommendations": [],
#                 "message": f"Chat with id '{chat_id}' does not exist"
#             }
#         )

#     # ✅ Fetch chat title
#     title_obj = db.query(Title).filter(Title.chat_id == chat_id).first()
#     chat_title = title_obj.title if title_obj else "Untitled Chat"

#     # ✅ Separate messages & recommendations
#     messages = [
#         {"id": r.id, "role": r.role, "content": r.content, "timestamp": r.timestamp}
#         for r in records if r.role is not None
#     ]

#     recommendations = [
#         {"id": r.id, "data": r.recommendation_data, "timestamp": r.timestamp}
#         for r in records if r.recommendation_data is not None
#     ]

#     return {
#         "error": False,
#         "chat_id": chat_id,
#         "title": chat_title,
#         "messages": messages,
#         "recommendations": recommendations,
#         "message": "Chat data retrieved successfully"
#     }



# # -------------------- Get Chat Recommendations --------------------
# @app.get("/chat/recommendations")
# def get_chat_recommendations(
#     chat_id: str = Query(..., description="Chat ID"),
#     db: Session = Depends(get_db)
# ):
#     rec_manager = RecommendationManager(db)
#     recs = rec_manager.get_recommendations(chat_id)
#     if not recs:
#         raise HTTPException(status_code=404, detail="No recommendations found")
#     return {"chat_id": chat_id, "recommendations": recs}


# # -------------------- Clear Chat Recommendations --------------------
# @app.delete("/chat/recommendations")
# def clear_chat_recommendations(
#     chat_id: str = Query(..., description="Chat ID"),
#     db: Session = Depends(get_db)
# ):
#     rec_manager = RecommendationManager(db)
#     rec_manager.clear_recommendations(chat_id)
#     return {"chat_id": chat_id, "message": "Recommendations cleared"}

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import tempfile
import os
import sys
from chatbot_module.database import get_db
from chatbot_module.user_manager import UserManager
from chatbot_module.chat_manager import ChatManager
from chatbot_module.bot_manager import BotManager
from chatbot_module.message_manager import MessageManager
from chatbot_module.recommendation_manager import RecommendationManager
from resume_analyzer.ai_analyzer import AIResumeAnalyzer
from resume_analyzer.resume_parser import ResumeParser
from resume_analyzer.scoring_engine import ATSScoringEngine
from resume_analyzer.strength_weakness_analyzer import StrengthWeaknessAnalyzer
from resume_analyzer.job_matcher import JobRoleMatcher
from resume_analyzer.pdf_extractor import PDFExtractor
from resume_analyzer.config import ATS_KEYWORDS, INDUSTRY_INSIGHTS

from chatbot_module.schemas import Title, ChatRecord

app = FastAPI(title="Chatbot Module API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize resume analyzer components
pdf_extractor = PDFExtractor()
resume_parser = ResumeParser()
scoring_engine = ATSScoringEngine()
strength_weakness_analyzer = StrengthWeaknessAnalyzer()
job_matcher = JobRoleMatcher()
ai_analyzer = AIResumeAnalyzer()

# Helper functions for resume analysis
def generate_executive_summary(sections, total_score, max_score, score_breakdown):
    """Generate executive summary from analysis results"""
    score_percentage = (total_score / max_score) * 100
    overall_assessment = score_breakdown.get('overall_assessment', {})
    
    return {
        "professional_profile": {
            "experience_level": sections.get('experience_level', 'Not determined'),
            "technical_skills_count": sections.get('skills_count', 0),
            "project_portfolio_size": sections.get('project_count', 0),
            "achievement_metrics": sections.get('quantified_achievements', 0),
            "technical_sophistication": sections.get('technical_sophistication', 'Basic')
        },
        "contact_presentation": {
            "email_address": "Present" if sections.get('email') else "Missing",
            "phone_number": "Present" if sections.get('phone') else "Missing",
            "education": "Documented" if sections.get('has_education') else "Missing",
            "resume_length": sections.get('word_count', 0),
            "action_verbs": sections.get('action_verb_count', 0)
        },
        "overall_assessment": {
            "score_percentage": score_percentage,
            "level": overall_assessment.get('level', 'Unknown'),
            "description": overall_assessment.get('description', ''),
            "recommendation": overall_assessment.get('recommendation', '')
        }
    }

def generate_detailed_scoring(score_breakdown):
    """Generate detailed scoring breakdown"""
    detailed_scores = {}
    
    for category, data in score_breakdown.items():
        if category == 'overall_assessment':
            continue
            
        category_name = category.replace('_', ' ').title()
        percentage = (data['score'] / data['max']) * 100
        
        detailed_scores[category] = {
            "score": data['score'],
            "max_score": data['max'],
            "percentage": percentage,
            "details": data.get('details', [])
        }
    
    return detailed_scores

def generate_improvement_plan(weaknesses_detailed):
    """Generate improvement plan from weaknesses"""
    # Group recommendations by priority
    critical_fixes = [w for w in weaknesses_detailed if w.get('fix_priority', '').startswith('CRITICAL')]
    high_priority = [w for w in weaknesses_detailed if w.get('fix_priority', '').startswith('HIGH')]
    medium_priority = [w for w in weaknesses_detailed if w.get('fix_priority', '').startswith('MEDIUM')]
    
    return {
        "critical_fixes": critical_fixes,
        "high_priority_improvements": high_priority,
        "medium_priority_enhancements": medium_priority,
        "implementation_timeline": [
            {"period": "Week 1-2", "task": "Fix critical contact and formatting issues", "priority": "🔴"},
            {"period": "Month 1-2", "task": "Enhance content quality and technical depth", "priority": "🟡"},
            {"period": "Month 2-3", "task": "Build project portfolio and quantified achievements", "priority": "🟠"},
            {"period": "Month 3-6", "task": "Advanced skill development and specialization", "priority": "🟢"}
        ]
    }

# Resume Analyzer Endpoints
@app.post("/analyze-resume")
async def analyze_resume(
    file: UploadFile = File(...), 
    target_role: str = None,
    api_key: str = None
):
    """
    Main endpoint to analyze a resume PDF and return comprehensive results
    """
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Set API key if provided
        if api_key:
            ai_analyzer.set_api_key(api_key)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract text from PDF
            resume_text = pdf_extractor.extract_text_from_pdf_path(tmp_file_path)
            
            if not resume_text:
                raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
            
            # Validate resume content
            is_valid, validation_message = pdf_extractor.validate_resume_content(resume_text)
            if not is_valid:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid resume content", "details": validation_message}
                )
            
            # Parse resume sections
            sections = resume_parser.extract_comprehensive_sections(resume_text)
            
            # Get AI analysis if API key is provided
            ai_comprehensive = None
            ai_targeted = None
            
            if api_key:
                try:
                    ai_comprehensive = ai_analyzer.get_comprehensive_ai_analysis(resume_text, target_role)
                    if target_role:
                        ai_targeted = ai_analyzer.get_targeted_role_analysis(resume_text, target_role)
                except Exception as e:
                    print(f"AI analysis error: {e}")
            
            # Calculate scores
            total_score, max_score, score_breakdown = scoring_engine.calculate_comprehensive_ats_score(
                resume_text, sections, target_role
            )
            
            # Get strengths and weaknesses
            strengths_detailed, weaknesses_detailed = strength_weakness_analyzer.analyze_comprehensive_strengths_weaknesses(
                resume_text, sections, target_role
            )
            
            # Get job market analysis
            job_analysis = job_matcher.get_comprehensive_job_analysis(resume_text, sections, target_role)
            
            # Prepare response
            response_data = {
                "success": True,
                "resume_metadata": {
                    "word_count": sections.get('word_count', 0),
                    "validation_message": validation_message,
                    "experience_level": sections.get('experience_level', 'Not determined'),
                    "skills_count": sections.get('skills_count', 0),
                    "project_count": sections.get('project_count', 0)
                },
                "executive_summary": generate_executive_summary(sections, total_score, max_score, score_breakdown),
                "detailed_scoring": generate_detailed_scoring(score_breakdown),
                "strengths_analysis": strengths_detailed,
                "weaknesses_analysis": weaknesses_detailed,
                "improvement_plan": generate_improvement_plan(weaknesses_detailed),
                "job_market_analysis": job_analysis,
                "ai_analysis": {
                    "comprehensive": ai_comprehensive,
                    "targeted": ai_targeted
                } if api_key else {"message": "API key required for AI analysis"}
            }
            
            return response_data
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/test-pdf-extraction")
async def test_pdf_extraction(file: UploadFile = File(...)):
    """
    Test endpoint to verify PDF extraction is working
    """
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract text from PDF
            resume_text = pdf_extractor.extract_text_from_pdf_path(tmp_file_path)
            
            if not resume_text:
                raise HTTPException(
                    status_code=400, 
                    detail="Failed to extract text from PDF"
                )
            
            # Validate resume content
            is_valid, validation_message = pdf_extractor.validate_resume_content(resume_text)
            
            return {
                "success": True,
                "extracted_text_length": len(resume_text),
                "word_count": len(resume_text.split()),
                "is_valid_resume": is_valid,
                "validation_message": validation_message,
                "text_preview": resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text
            }
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction test failed: {str(e)}")

# -------------------- Chat Creation --------------------
@app.post("/chat/create")
def create_chat(user_id: str = Query(..., description="User ID"), db: Session = Depends(get_db)):
    user_manager = UserManager(db)
    chat_manager = ChatManager(db)

    # ✅ Auto-register user if not exists
    user, created = user_manager.register_user(user_id)

    # ✅ Create chat
    chat = chat_manager.create_chat(user_id)
    return {
        "user_id": user.id,
        "chat_id": chat.id,
        "created_at": chat.created_at,
        "message": "User created and chat started" if created else "Chat started"
    }

# -------------------- List User Chats --------------------
@app.get("/chat/list")
def list_chats(user_id: str = Query(..., description="User ID"), db: Session = Depends(get_db)):
    user_manager = UserManager(db)
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_manager = ChatManager(db)
    chats = chat_manager.get_chats(user_id)

    return [
        {
            "chat_id": c.id,
            "title": c.title.title if c.title else "Untitled Chat",  # ✅ Add chat title
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "status": c.status
        }
        for c in chats
    ]

# -------------------- Send Message --------------------
@app.post("/chat/send")
def send_message(
    user_id: str = Query(..., description="User ID"),
    chat_id: str = Query(..., description="Chat ID"),
    message: str = Body(..., embed=True, description="User message"),
    db: Session = Depends(get_db)
):
    user_manager = UserManager(db)
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bot_manager = BotManager(db)
    try:
        result = bot_manager.process_message(user_id, chat_id, message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Ensure recommendations is always a list
    recommendations = result.get("recommendations", [])
    if recommendations is None:
        recommendations = []
    
    # Also try to get any stored recommendations
    if not recommendations:
        recommendations = bot_manager.get_recommendations(chat_id)

    # ✅ Fetch chat title
    title_obj = db.query(Title).filter(Title.chat_id == chat_id).first()
    chat_title = title_obj.title if title_obj else "Untitled Chat"

    return {
        "chat_id": chat_id,
        "title": chat_title,
        "user_message": message,
        "bot_response": result["response"],
        "recommendations": recommendations
    }

@app.get("/chat/messages")
def get_chat_messages(
    chat_id: str = Query(..., description="Chat ID"),
    db: Session = Depends(get_db)
):
    # ✅ Fetch all chat records (both messages & recommendations)
    records = db.query(ChatRecord).filter(ChatRecord.chat_id == chat_id).all()
    if not records:
        raise HTTPException(
            status_code=404,
            detail={
                "error": True,
                "chat_id": chat_id,
                "title": "",
                "messages": [],
                "recommendations": [],
                "message": f"Chat with id '{chat_id}' does not exist"
            }
        )

    # ✅ Fetch chat title
    title_obj = db.query(Title).filter(Title.chat_id == chat_id).first()
    chat_title = title_obj.title if title_obj else "Untitled Chat"

    # ✅ Separate messages & recommendations
    messages = [
        {"id": r.id, "role": r.role, "content": r.content, "timestamp": r.timestamp}
        for r in records if r.role is not None
    ]

    recommendations = [
        {"id": r.id, "data": r.recommendation_data, "timestamp": r.timestamp}
        for r in records if r.recommendation_data is not None
    ]

    return {
        "error": False,
        "chat_id": chat_id,
        "title": chat_title,
        "messages": messages,
        "recommendations": recommendations,
        "message": "Chat data retrieved successfully"
    }

# -------------------- Get Chat Recommendations --------------------
@app.get("/chat/recommendations")
def get_chat_recommendations(
    chat_id: str = Query(..., description="Chat ID"),
    db: Session = Depends(get_db)
):
    rec_manager = RecommendationManager(db)
    recs = rec_manager.get_recommendations(chat_id)
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations found")
    return {"chat_id": chat_id, "recommendations": recs}

# -------------------- Clear Chat Recommendations --------------------
@app.delete("/chat/recommendations")
def clear_chat_recommendations(
    chat_id: str = Query(..., description="Chat ID"),
    db: Session = Depends(get_db)
):
    rec_manager = RecommendationManager(db)
    rec_manager.clear_recommendations(chat_id)
    return {"chat_id": chat_id, "message": "Recommendations cleared"}
