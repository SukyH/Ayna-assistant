from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

Base = declarative_base()

class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, index=True)
    profile_snapshot = Column(Text)  # Optional: store profile state
    job_snapshot = Column(Text)      # Optional: store job description state
    overall_score = Column(Float)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    feedback_text = Column(Text)     # Plain feedback
    timestamp = Column(DateTime, default=datetime.utcnow)


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    url = Column(String, nullable=True) 
    status = Column(String, default="Saved")
    notes = Column(Text, nullable=True)
    reminder_date = Column(DateTime, nullable=True)
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)  

    # Models
class Field(BaseModel):
    field_id: str
    label: str
    type: Optional[str] = "text"
    name: Optional[str] = ""
    placeholder: Optional[str] = ""

class ProfileData(BaseModel):
    fullName: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    portfolio: Optional[str] = ""
    summary: Optional[str] = ""
    skills: Optional[List[str]] = []
    education: Optional[List[Dict]] = []
    experience: Optional[List[Dict]] = []
    projects: Optional[List[Dict]] = []
    licenses: Optional[List[Dict]] = []

class AutofillRequest(BaseModel):
    fields: List[Field]
    profile: ProfileData
    memory: Optional[Dict[str, str]] = {}  # Added

class JobApplicationIn(BaseModel):
    title: str
    company: str
    url: Optional[str] = None 
    status: str = "Saved"
    notes: Optional[str] = None
    reminder_date: Optional[datetime] = None
    feedback: Optional[str] = None

class JobApplicationOut(JobApplicationIn):
    id: int
    timestamp: datetime

class GenericInput(BaseModel):
    data: Any

class JobURL(BaseModel):
    url: str

class JobTextInput(BaseModel):
    text: str

class ApplicationPayload(BaseModel):
    profile: dict
    job: dict
    resume: dict | None = None

class ResumeRefinementPayload(BaseModel):
    profile: dict
    job: dict
    resume: str
    feedback: str

class CoverLetterRefinementPayload(BaseModel):
    profile: dict
    job: dict
    resume: str | None = None
    coverletter: str
    feedback: str

class MatchScorePayload(BaseModel):
    profile: Dict[str, Any]
    job: Dict[str, Any]

class FeedbackIn(BaseModel):
    profile_snapshot: str | None = None
    job_snapshot: str | None = None
    overall_score: float
    skills_score: float
    experience_score: float
    education_score: float
    feedback_text: str

# Request model
class LicenseItem(BaseModel):
    title: Optional[str] = ""
    description: Optional[str] = ""
    issueDate: Optional[str] = ""
    expiryDate: Optional[str] = ""

class EducationItem(BaseModel):
    school: Optional[str] = ""
    degree: Optional[str] = ""
    field: Optional[str] = ""
    startDate: Optional[str] = ""
    endDate: Optional[str] = ""
    gpa: Optional[str] = ""

class ExperienceItem(BaseModel):
    company: Optional[str] = ""
    position: Optional[str] = ""
    startDate: Optional[str] = ""
    endDate: Optional[str] = ""
    description: Optional[str] = ""

class ProjectItem(BaseModel):
    name: Optional[str] = ""
    techStack: Optional[str] = ""
    description: Optional[str] = ""
    link: Optional[str] = ""

class EnrichedProfile(BaseModel):
    fullName: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    portfolio: Optional[str] = ""
    summary: Optional[str] = ""
    education: Optional[List[EducationItem]] = []
    experience: Optional[List[ExperienceItem]] = []
    projects: Optional[List[ProjectItem]] = []
    skills: Optional[List[str]] = []
    licenses: Optional[List[LicenseItem]] = []

class TextInput(BaseModel):
    text: str
    