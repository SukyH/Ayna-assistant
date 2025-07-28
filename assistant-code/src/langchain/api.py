# api.py
from fastapi import FastAPI,APIRouter, Depends, HTTPException,UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from src.langchain.profile_enrichment import profile_prompt
from src.langchain.job_scraper import fetch_job_description
from src.langchain.jd_parser import parse_job_posting
from src.langchain.main import get_llm
from pydantic import BaseModel
from src.langchain.resume_generator import get_resume_chain,generate_resume_with_retry,generate_pdf_from_doc,get_resume_refinement_chain,refine_resume_with_retry
from src.langchain.coverletter_generator import get_coverletter_chain,generate_coverletter_with_retry,get_coverletter_refinement_chain,refine_coverletter_with_retry
from src.langchain.job_matcher import match_score
from src.langchain.autofill import  smart_autofill, field_usage_tracker,llm, clf, embedder
from src.langchain.models import AutofillRequest,ProfileData,Field,JobApplicationIn,JobApplicationOut,GenericInput,JobURL,JobTextInput,ApplicationPayload,ResumeRefinementPayload,CoverLetterRefinementPayload,MatchScorePayload,FeedbackIn,LicenseItem,EducationItem,ExperienceItem,ProjectItem,TextInput,EnrichedProfile
from fastapi.responses import StreamingResponse
import io
import json
import multiprocessing
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from src.Database.Database import engine, SessionLocal
from .models import Base, JobApplication, Feedback
from datetime import datetime
import joblib
from sentence_transformers import SentenceTransformer
from langchain.schema import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
import logging
import re
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import joblib
import numpy as np
import asyncio
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import gc
from contextlib import asynccontextmanager

# Simulated server-side persistent memory (replace with DB or Redis in production)
persistent_autofill_memory = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    multiprocessing.set_start_method("fork")

app = FastAPI()
router = APIRouter()
app.include_router(router)


# Allow frontend/extension requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)



@app.post("/autofill")
async def autofill(request: AutofillRequest) -> Dict[str, str]:
    """
    Enhanced autofill endpoint with async processing and better classification
    """
    start_time = time.time()
    
    try:
        # Validate request
        if not request.fields:
            logger.warning("⚠️ No fields provided in request")
            return {}
        
        if not request.profile:
            logger.warning("⚠️ No profile provided in request")
            return {}
        
        logger.info(f"🚀 Starting autofill for {len(request.fields)} fields")
        
        # Use the enhanced smart_autofill function
        results = await smart_autofill(request)
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Autofill completed in {processing_time:.2f}s")
        logger.info(f"🎯 Returning {len(results)} autofill values")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Autofill failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Autofill processing failed: {str(e)}")

@app.post("/autofill/batch")
async def autofill_batch(requests: list[AutofillRequest]) -> Dict[str, Dict[str, str]]:
    """
    Batch autofill endpoint for processing multiple requests
    """
    if not requests:
        return {}
    
    logger.info(f"🚀 Processing batch of {len(requests)} autofill requests")
    
    try:
        # Process all requests concurrently
        tasks = [smart_autofill(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results
        batch_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Batch request {i} failed: {str(result)}")
                batch_results[f"request_{i}"] = {}
            else:
                batch_results[f"request_{i}"] = result
        
        logger.info(f"✅ Batch processing completed")
        return batch_results
        
    except Exception as e:
        logger.error(f"❌ Batch autofill failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch autofill processing failed: {str(e)}")

@app.get("/autofill/memory")
async def get_memory_stats():
    """
    Get memory statistics and cached values
    """
    try:
 
        stats = {
            "memory_entries": len(persistent_autofill_memory),
            "field_usage_entries": len(field_usage_tracker),
            "memory_keys": list(persistent_autofill_memory.keys()),
            "recent_memory": {
                k: v for k, v in list(persistent_autofill_memory.items())[-10:]
            }
        }
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory statistics")

@app.delete("/autofill/memory")
async def clear_memory():
    """
    Clear autofill memory cache
    """
    try:
        
        memory_count = len(persistent_autofill_memory)
        usage_count = len(field_usage_tracker)
        
        persistent_autofill_memory.clear()
        field_usage_tracker.clear()
        
        logger.info(f"🧹 Cleared {memory_count} memory entries and {usage_count} usage entries")
        
        return {
            "message": "Memory cleared successfully",
            "cleared_memory_entries": memory_count,
            "cleared_usage_entries": usage_count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to clear memory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear memory")

@app.get("/autofill/health")
async def health_check():
    """
    Health check endpoint for autofill service
    """
    try:
        
        health_status = {
            "status": "healthy",
            "llm_available": llm is not None,
            "ml_models_available": clf is not None and embedder is not None,
            "timestamp": time.time()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Add middleware for request timing
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


parser = JsonOutputParser(pydantic_object=EnrichedProfile)

# Text enrichment endpoint
@app.post("/enrich-text")
async def enrich_text_endpoint(request: dict):
    try:
        text = request.get("text", "")
        if not text.strip():
            return {"error": "No text provided"}
        
        llm = get_llm()
        parser = JsonOutputParser()
        chain = profile_prompt | llm | parser
        
        result = chain.invoke({"profile_json": text})
        
        # Ensure result is properly formatted
        if isinstance(result, dict):
            # Validate required fields exist
            required_fields = ["fullName", "email", "phone", "location", "linkedin", 
                             "github", "portfolio", "summary", "education", "experience", 
                             "projects", "skills", "licenses"]
            
            for field in required_fields:
                if field not in result:
                    if field in ["education", "experience", "projects", "licenses"]:
                        result[field] = []
                    elif field == "skills":
                        result[field] = []
                    else:
                        result[field] = ""
            
            return {"enriched": result}
        else:
            return {"error": "Invalid response format from LLM"}
            
    except Exception as e:
        print(f"Error in enrich_text_endpoint: {str(e)}")
        return {"error": f"Enrichment failed: {str(e)}"}

# Profile enrichment endpoint  
@app.post("/enrich-profile")
async def enrich_profile_endpoint(profile: dict):
    try:
        llm = get_llm()
        parser = JsonOutputParser()
        chain = profile_prompt | llm | parser
        
        # Convert profile to JSON string for the prompt
        profile_json = json.dumps(profile, indent=2)
        result = chain.invoke({"profile_json": profile_json})
        
        # Ensure result is properly formatted
        if isinstance(result, dict):
            # Validate required fields exist
            required_fields = ["fullName", "email", "phone", "location", "linkedin", 
                             "github", "portfolio", "summary", "education", "experience", 
                             "projects", "skills", "licenses"]
            
            for field in required_fields:
                if field not in result:
                    if field in ["education", "experience", "projects", "licenses"]:
                        result[field] = []
                    elif field == "skills":
                        result[field] = []
                    else:
                        result[field] = ""
            
            return {"enriched": result}
        else:
            return {"error": "Invalid response format from LLM"}
            
    except Exception as e:
        print(f"Error in enrich_profile_endpoint: {str(e)}")
        return {"error": f"Enrichment failed: {str(e)}"}


@app.post("/submit-feedback")
def submit_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    feedback_entry = Feedback(**payload.dict())
    db.add(feedback_entry)
    db.commit()
    db.refresh(feedback_entry)
    return {"status": "success", "id": feedback_entry.id}

@app.post("/match-score")
async def get_match_score(payload: MatchScorePayload):
    try:
        score_result = match_score(payload.dict())
        return score_result
    except Exception as e:
        return {"error": str(e)}

@app.post("/refine-resume")
async def refine_resume_api(payload: ResumeRefinementPayload):
    job_clean = dict(payload.job)
    job_clean.pop("raw", None)
    chain = get_resume_refinement_chain()
    input_data = {
        "profile": payload.profile,
        "job": job_clean,
        "resume": payload.resume,
        "feedback": payload.feedback,
    }
    refined = await refine_resume_with_retry(chain, input_data)
    return {"refined_resume": refined}

@app.post("/refine-coverletter")
async def refine_coverletter_api(payload: CoverLetterRefinementPayload):
    job_clean = dict(payload.job)
    job_clean.pop("raw", None)
    chain = get_coverletter_refinement_chain()
    input_data = {
        "profile": payload.profile,
        "job": job_clean,
        "resume": payload.resume or "",
        "coverletter": payload.coverletter,
        "feedback": payload.feedback,
    }
    refined = await refine_coverletter_with_retry(chain, input_data)
    return {"refined_coverletter": refined}


# Resume generation endpoint with retry
@app.post("/generate-resume")
async def generate_resume_api(payload: ApplicationPayload):
    job_clean = dict(payload.job)
    job_clean.pop("raw", None)

    print("Sending to resume generator:", job_clean)
    chain = get_resume_chain()
    print(job_clean)
    input_data = {
        "profile": payload.profile,
        "job": job_clean,
        "resume": payload.resume or {},
    }
    resume = await generate_resume_with_retry(chain, input_data)
    return {"resume": resume}

@app.post("/download-resume-pdf")
async def download_resume_pdf(payload: ApplicationPayload):
    chain = get_resume_chain()
    input_data = {
        "profile": payload.profile,
        "job": payload.job,
        "resume": payload.resume or {},
    }
    resume_text = await generate_resume_with_retry(chain, input_data)
    pdf_bytes = generate_pdf_from_doc(resume_text, title="Generated Resume", parse_sections=True)
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=resume.pdf"
    })

@app.post("/download-coverletter-pdf")
async def download_coverletter_pdf(payload: ApplicationPayload):
    chain = get_coverletter_chain()
    coverletter_text = await chain.ainvoke({
        "profile": payload.profile,
        "job": payload.job,
        "resume": payload.resume or {},
    })
    pdf_bytes = generate_pdf_from_doc(coverletter_text, parse_sections=False)
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=coverletter.pdf"
    })


@app.post("/generate-coverletter")
async def generate_coverletter_api(payload: ApplicationPayload):
    job_clean = dict(payload.job)
    job_clean.pop("raw", None)

    print("Sending to resume generator:", job_clean)
    chain = get_coverletter_chain()
    input_data = {
        "profile": payload.profile,
        "job": job_clean,
        "resume": payload.resume or {},
    }
    coverletter = await generate_coverletter_with_retry(chain, input_data)
    return {"coverletter": coverletter}


#Job scraping endpoint
@app.post("/scrape-job")
async def scrape_job_endpoint(input: JobURL):
    jd_text = await fetch_job_description(input.url)
    parsed = parse_job_posting(jd_text)
    return parsed

@app.post("/parse-job-text")
async def parse_job_text(input: JobTextInput):
    return parse_job_posting(input.text)

@app.post("/job-tracker/add", response_model=JobApplicationOut)
def add_job_application(application: JobApplicationIn, db: Session = Depends(get_db)):
    print("Received job:", application)
    db_app = JobApplication(**application.dict())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@app.get("/job-tracker/all", response_model=List[JobApplicationOut])
def list_job_applications(db: Session = Depends(get_db)):
    return db.query(JobApplication).order_by(JobApplication.timestamp.desc()).all()

@app.put("/job-tracker/update/{app_id}", response_model=JobApplicationOut)
def update_job_application(app_id: int, application: JobApplicationIn, db: Session = Depends(get_db)):
    db_app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    for key, value in application.dict().items():
        setattr(db_app, key, value)
    
    db.commit()
    db.refresh(db_app)
    return db_app

@app.delete("/job-tracker/delete/{app_id}")
def delete_job_application(app_id: int, db: Session = Depends(get_db)):
    db_app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(db_app)
    db.commit()
    return {"status": "deleted"}

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.langchain.api:app",  # ✅ Correct module path and app instance
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,  # Single worker to prevent resource conflicts
        loop="asyncio",
        access_log=True,
        log_level="info",
        timeout_keep_alive=30,
        limit_concurrency=50,  # Limit concurrent connections
        limit_max_requests=1000  # Restart worker after 1000 requests
    )

