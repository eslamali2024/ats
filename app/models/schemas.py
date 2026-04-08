from pydantic import BaseModel
from typing import List, Optional


class SkillMatch(BaseModel):
    skill: str
    confidence: float
    category: str


class EducationEntry(BaseModel):
    degree: str
    institution: str
    year: str


class WorkExperienceEntry(BaseModel):
    job_title: str
    company: str
    duration: str


class PersonalInfo(BaseModel):
    fullname: str
    email: str
    phone: str
    age: Optional[int]
    birth_date: str
    location: str
    summary: str
    education: List[EducationEntry]
    work_experience: List[WorkExperienceEntry]
    extraction_confidence: float
    expertise_years: Optional[float]


class CVAnalysisResponse(BaseModel):
    status: str
    extracted_text: str
    personal_info: PersonalInfo
    skills_found: List[str]
    technical_skills: List[str]
    framework_skills: List[str]
    language_skills: List[str]
    total_skills_count: int
    has_desired_skills: bool
    match_score: float


class HealthResponse(BaseModel):
    status: str
    version: str
