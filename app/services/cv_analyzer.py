"""
Main CV Analysis Service
"""
from typing import Dict, Tuple
from app.utils.pdf_extractor import PDFExtractor
from app.utils.skill_extractor import extract_skills_from_text
from app.utils.personal_info_extractor import extract_personal_info
from app.models.schemas import CVAnalysisResponse, SkillMatch, PersonalInfo, EducationEntry, WorkExperienceEntry

 
class CVAnalyzerService:
    """Service for analyzing CVs and extracting skills."""

    def __init__(self):
        self.pdf_extractor = PDFExtractor()

    def analyze_pdf(self, file_bytes: bytes, filename: str = "", job_requisition_skills: list = None) -> CVAnalysisResponse:
        """
        Analyze a PDF CV file.
        
        Args:
            file_bytes: PDF file as bytes
            filename: Original filename (for logging)
            
        Returns:
            CVAnalysisResponse with extracted data
        """
        try:
            # Validate PDF
            if not self.pdf_extractor.validate_pdf(file_bytes):
                return CVAnalysisResponse(
                    status="error",
                    extracted_text="",
                    personal_info=PersonalInfo(
                        fullname="", email="", phone="", age=None, 
                        birth_date="", location="", summary="", 
                        education=[], work_experience=[], extraction_confidence=0.0,
                        expertise_years=None
                    ),
                    skills_found=[],
                    technical_skills=[],
                    framework_skills=[],
                    language_skills=[],
                    total_skills_count=0,
                    has_desired_skills=False,
                    match_score=0.0
                )

            # Extract text from PDF
            extracted_text = self.pdf_extractor.extract_text_from_bytes(file_bytes)

            if not extracted_text:
                return CVAnalysisResponse(
                    status="error",
                    extracted_text="",
                    personal_info=PersonalInfo(
                        fullname="", email="", phone="", age=None, 
                        birth_date="", location="", summary="", 
                        education=[], work_experience=[], extraction_confidence=0.0,
                        expertise_years=None
                    ),
                    skills_found=[],
                    technical_skills=[],
                    framework_skills=[],
                    language_skills=[],
                    total_skills_count=0,
                    has_desired_skills=False,
                    match_score=0.0
                )

            # Extract skills — pass job requisition skills for dynamic matching
            skills_data = extract_skills_from_text(extracted_text, job_requisition_skills or [])
            
            # Extract personal information
            personal_info_data = extract_personal_info(extracted_text)
            
            # Create PersonalInfo object
            education_list = [
                EducationEntry(
                    degree=edu.get("degree", ""),
                    institution=edu.get("institution", ""),
                    year=edu.get("year", "")
                )
                for edu in personal_info_data.get("education", [])
            ]
            
            work_exp_list = [
                WorkExperienceEntry(
                    job_title=exp.get("job_title", ""),
                    company=exp.get("company", ""),
                    duration=exp.get("duration", "")
                )
                for exp in personal_info_data.get("work_experience", [])
            ]
            
            personal_info = PersonalInfo(
                fullname=personal_info_data.get("fullname", ""),
                email=personal_info_data.get("email", ""),
                phone=personal_info_data.get("phone", ""),
                age=personal_info_data.get("age"),
                birth_date=personal_info_data.get("birth_date", ""),
                location=personal_info_data.get("location", ""),
                summary=personal_info_data.get("summary", ""),
                education=education_list,
                work_experience=work_exp_list,
                extraction_confidence=personal_info_data.get("extraction_confidence", 0.0),
                expertise_years=personal_info_data.get("expertise_years")
            )

            # Build response - handle both string and dict formats
            skills_found_list = []
            if skills_data.get("technical_skills"):
                for s in skills_data.get("technical_skills", []):
                    try:
                        if isinstance(s, dict):
                            skill_name = s.get("skill", "")
                            skill_conf = s.get("confidence", 0.8)
                        else:
                            skill_name = str(s) if s else ""
                            skill_conf = 0.8
                        
                        if skill_name:
                            skills_found_list.append(SkillMatch(
                                skill=skill_name,
                                confidence=float(skill_conf),
                                category="technical"
                            ))
                    except Exception:
                        continue
            
            # Extract skill names safely
            technical_skills_list = []
            framework_skills_list = []
            language_skills_list = []
            
            for s in skills_data.get("technical_skills", []):
                try:
                    skill_name = s["skill"] if isinstance(s, dict) else str(s)
                    if skill_name:
                        technical_skills_list.append(skill_name)
                except Exception:
                    continue
            
            for s in skills_data.get("framework_skills", []):
                try:
                    skill_name = s["skill"] if isinstance(s, dict) else str(s)
                    if skill_name:
                        framework_skills_list.append(skill_name)
                except Exception:
                    continue
            
            for s in skills_data.get("language_skills", []):
                try:
                    skill_name = s["skill"] if isinstance(s, dict) else str(s)
                    if skill_name:
                        language_skills_list.append(skill_name)
                except Exception:
                    continue
            
            all_found_skills = [s[0] for s in skills_data.get("skills_found", [])] if isinstance(skills_data.get("skills_found"), list) else []

            response = CVAnalysisResponse(
                status="success",
                extracted_text=extracted_text[:1000],  # Limit to first 1000 chars
                personal_info=personal_info,
                skills_found=all_found_skills,
                technical_skills=technical_skills_list,
                framework_skills=framework_skills_list,
                language_skills=language_skills_list,
                total_skills_count=skills_data.get("total_skills_count", 0),
                has_desired_skills=skills_data.get("has_desired_skills", False),
                match_score=float(skills_data.get("match_score", 0.0))
            )

            return response

        except Exception as e:
            return CVAnalysisResponse(
                status=f"error: {str(e)}",
                extracted_text="",
                personal_info=PersonalInfo(
                    fullname="", email="", phone="", age=None, 
                    birth_date="", location="", summary="", 
                    education=[], work_experience=[], extraction_confidence=0.0,
                    expertise_years=None
                ),
                skills_found=[],
                technical_skills=[],
                framework_skills=[],
                language_skills=[],
                total_skills_count=0,
                has_desired_skills=False,
                match_score=0.0
            )

    def filter_candidates_by_skills(self, candidates_data: list, min_score: float = 0.5) -> list:
        """
        Filter candidates based on skill match score.
        
        Args:
            candidates_data: List of candidate data with CV analysis results
            min_score: Minimum match score to include candidate (0-1)
            
        Returns:
            Filtered list of candidates
        """
        return [
            candidate for candidate in candidates_data
            if candidate.get("match_score", 0) >= (min_score * 100)
        ]
