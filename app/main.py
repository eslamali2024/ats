"""
FastAPI CV Analysis Service
Main application file
"""
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from app.services.cv_analyzer import CVAnalyzerService
from app.models.schemas import HealthResponse, CVAnalysisResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CV Analyzer Service",
    description="Professional CV analysis service with skill extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://127.0.0.1:8000",
        # "http://localhost:8000",
        "https://smarttel-erp.com",
        "http://smarttel-erp.com",
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize service
cv_analyzer = CVAnalyzerService()

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.post("/analyze-cv", response_model=CVAnalysisResponse)
async def analyze_cv(
    file: UploadFile = File(...),
    min_score: float = Query(0.0, ge=0, le=100),
    job_requisition_skills: str = Form("[]"),  # JSON array of skill name strings from the DB
):
    """
    Analyze a CV PDF and extract skills.
    
    Args:
        file: PDF file to analyze
        min_score: Minimum match score filter (0-100)
        
    Returns:
        CVAnalysisResponse with extracted skills and analysis
    """
    try:
        # Validate file type
        # if file.content_type not in ["application/pdf"]:
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Only PDF files are allowed"
        #     )

        # Read file
        file_bytes = await file.read()

        # Check file size
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )

        # Parse job requisition skills from JSON form field
        try:
            skills_list = json.loads(job_requisition_skills) if job_requisition_skills else []
            if not isinstance(skills_list, list):
                skills_list = []
        except (json.JSONDecodeError, TypeError):
            skills_list = []

        # Analyze CV
        result = cv_analyzer.analyze_pdf(file_bytes, file.filename, skills_list)

        logger.info(f"CV analyzed successfully: {file.filename}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing CV: {str(e)}"
        )


@app.post("/batch-analyze")
async def batch_analyze(files: list[UploadFile] = File(...)):
    """
    Analyze multiple CVs in batch.
    
    Args:
        files: Multiple PDF files to analyze
        
    Returns:
        List of analysis results
    """
    try:
        results = []
        
        for file in files:
            if file.content_type not in ["application/pdf"]:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Only PDF files are allowed"
                })
                continue

            file_bytes = await file.read()
            
            if len(file_bytes) > MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"File size exceeds maximum"
                })
                continue

            result = cv_analyzer.analyze_pdf(file_bytes, file.filename)
            results.append({
                "filename": file.filename,
                **result.dict()
            })

        logger.info(f"Batch analysis completed for {len(results)} files")
        return JSONResponse(content={"results": results})

    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch analysis: {str(e)}"
        )


@app.get("/desired-skills")
async def get_desired_skills():
    """Return all skills currently loaded from the database (cached)."""
    from app.utils.db_client import get_skills_db
    skills_db = get_skills_db()
    return JSONResponse(content={
        "status": "success",
        "total":  len(skills_db),
        "skills": list(skills_db.keys()),
        "note":   "Skills are fetched from the Laravel database and cached for 5 minutes."
    })


@app.post("/skills/refresh")
async def refresh_skills_cache():
    """Force a reload of the skills cache from the Laravel database."""
    from app.utils.db_client import invalidate_cache, get_skills_db
    invalidate_cache()
    skills_db = get_skills_db()   # immediately re-fetch
    return JSONResponse(content={
        "status": "success",
        "message": f"Skills cache refreshed. {len(skills_db)} skills loaded from database."
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
