from typing import Dict, Any, List
from dataclasses import dataclass
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json
import logging
from src.langchain.main import get_llm

logger = logging.getLogger(__name__)

class SectionScore(BaseModel):
    """Individual section scoring results"""
    score: float = Field(description="Score from 0-100")
    reasoning: str = Field(description="Detailed reasoning for the score")
    strengths: List[str] = Field(description="Key strengths in this section")
    gaps: List[str] = Field(description="Key gaps or missing elements")
    missing_keywords: List[str] = Field(description="Important missing keywords/skills")

class MatchScoreResult(BaseModel):
    """Complete LLM-based matching results"""
    overall_score: float = Field(description="Overall match score from 0-100")
    skills_score: SectionScore = Field(description="Skills section analysis")
    experience_score: SectionScore = Field(description="Experience section analysis") 
    education_score: SectionScore = Field(description="Education section analysis")
    overall_reasoning: str = Field(description="Summary reasoning for overall score")
    recommendations: List[str] = Field(description="Top 3-5 actionable recommendations")
    application_probability: str = Field(description="Estimated success probability category")

@dataclass
class LLMMatchConfig:
    """Configuration for LLM-based matching"""
    skills_weight: float = 0.45
    experience_weight: float = 0.40
    education_weight: float = 0.15
    temperature: float = 0.3  # Lower for more consistent scoring
    max_retries: int = 3

class LLMJobMatcher:
    """LLM-based job matching system with structured output"""
    
    def __init__(self, config: LLMMatchConfig = None):
        self.config = config or LLMMatchConfig()
        self.llm = get_llm()
        self.parser = PydanticOutputParser(pydantic_object=MatchScoreResult)
        self._setup_prompt()
        
    def _setup_prompt(self):
        """Initialize the comprehensive matching prompt"""
        self.match_prompt = PromptTemplate(
            input_variables=[
                "profile_skills", "profile_experience", "profile_education",
                 "resume_text",
                "job_skills", "job_experience", "job_education",
                "skills_weight", "experience_weight", "education_weight"
            ],
            template="""You are an expert HR analyst and career advisor.

Your job is to evaluate a candidate's suitability for a job role based on:
- Their structured profile (skills, experience, education)
- Their resume content (raw or parsed text)
- The job description (skills, responsibilities, and education requirements)
Score each section from 0 to 100. Then provide an overall match score based on the weights provided. 
For each section (skills, experience, education):
- Explain clearly why the candidate received their score including their strength and gaps.
- Be specific: reference tools, terminology, or examples mentioned in the profile and how they relate to the job requirements.
- Avoid vague phrases like "needs improvement" — instead, highlight exact weaknesses or missing details.
- Give practical improvement suggestions (e.g., tools to learn, courses to take, how to reword a project).
CANDIDATE PROFILE:
Skills: {profile_skills}
Experience: {profile_experience}
Education: {profile_education}

RESUME CONTENT (additional context):
{resume_text}

JOB REQUIREMENTS:
Required Skills: {job_skills}
Required Experience: {job_experience}
Required Education: {job_education}

SCORING WEIGHTS:
- Skills: {skills_weight}%
- Experience: {experience_weight}%
- Education: {education_weight}%

 Return ONLY valid JSON in this exact format (but with real values, not placeholders):
{{
  "overall_score": float,
  "skills_score": {{
    "score": float,
    "reasoning": string,
    "strengths": [string],
    "gaps": [string],
    "missing_keywords": [string]
  }},
  "experience_score": {{
    "score": float,
    "reasoning": string,
    "strengths": [string],
    "gaps": [string],
    "missing_keywords": [string]
  }},
  "education_score": {{
    "score": float,
    "reasoning": string,
    "strengths": [string],
    "gaps": [string],
    "missing_keywords": [string]
  }},
  "overall_reasoning": string,
  "recommendations": [string],
  "application_probability": string
}}

Do not include example values. Fill in all fields with real analysis based on the profile and job. Do not return any explanation or markdown — only the JSON object.""",
            partial_variables={
                "skills_weight": int(self.config.skills_weight * 100),
                "experience_weight": int(self.config.experience_weight * 100),
                "education_weight": int(self.config.education_weight * 100)
            }
        )
        
        self.llm_chain = self.match_prompt | self.llm | StrOutputParser()

    def _prepare_profile_text(self, profile: Dict[str, Any]) -> Dict[str, str]:
        """Convert structured profile data to text for LLM analysis"""
        
        # Skills (already a list)
        skills_text = ", ".join(profile.get("skills", [])) if profile.get("skills") else "No skills listed"
        
        # Experience (convert from structured format)
        experience_data = profile.get("experience", [])
        if isinstance(experience_data, list) and experience_data:
            exp_parts = []
            for exp in experience_data:
                exp_text = f"{exp.get('position', 'Unknown Position')} at {exp.get('company', 'Unknown Company')}"
                if exp.get('description'):
                    exp_text += f": {exp.get('description')}"
                if exp.get('startDate') or exp.get('endDate'):
                    dates = f"({exp.get('startDate', '')} - {exp.get('endDate', 'present')})"
                    exp_text += f" {dates}"
                exp_parts.append(exp_text)
            experience_text = ". ".join(exp_parts)
        else:
            experience_text = str(experience_data) if experience_data else "No experience listed"
        
        # Education (convert from structured format)
        education_data = profile.get("education", [])
        if isinstance(education_data, list) and education_data:
            edu_parts = []
            for edu in education_data:
                edu_text = f"{edu.get('degree', 'Unknown Degree')} in {edu.get('field', 'Unknown Field')} from {edu.get('school', 'Unknown School')}"
                if edu.get('startDate') or edu.get('endDate'):
                    dates = f"({edu.get('startDate', '')} - {edu.get('endDate', '')})"
                    edu_text += f" {dates}"
                if edu.get('gpa'):
                    edu_text += f", GPA: {edu.get('gpa')}"
                edu_parts.append(edu_text)
            education_text = ". ".join(edu_parts)
        else:
            education_text = str(education_data) if education_data else "No education listed"
            
        return {
            "skills": skills_text,
            "experience": experience_text,
            "education": education_text
        }

    def analyze_match(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract and prepare data
            profile = payload.get("profile", {})
            resume = payload.get("resume", "") 
            job = payload.get("job", {})
            
            # Convert profile to text format
            profile_text = self._prepare_profile_text(profile)
            
            # Prepare job requirements (assume they're already strings from the parser)
            job_skills = ", ".join(job.get("skills", [])) if isinstance(job.get("skills"), list) else str(job.get("skills", ""))
            job_experience = str(job.get("experience", ""))
            job_education = str(job.get("education", ""))
            
            # Validate inputs
            if not any([profile_text["skills"], profile_text["experience"], profile_text["education"]]):
                raise ValueError("Profile appears to be empty")
                
            if not any([job_skills, job_experience, job_education]):
                raise ValueError("Job requirements appear to be empty")
            
            # Retry logic for LLM analysis
            for attempt in range(self.config.max_retries):
                try:
                    result_str = self.llm_chain.invoke({
                        "profile_skills": profile_text["skills"],
                        "profile_experience": profile_text["experience"],
                        "profile_education": profile_text["education"],
                        "resume_text": resume or "No resume provided.",
                        "job_skills": job_skills,
                        "job_experience": job_experience,
                        "job_education": job_education
                    })
                    
                    # Parse JSON manually
                    result_dict = json.loads(result_str)
                    
                    # Convert to backward-compatible format
                    return self._convert_to_legacy_format(result_dict, profile, job)
                    
                except Exception as e:
                    logger.warning(f"LLM analysis attempt {attempt + 1} failed: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    continue
                    
        except Exception as e:
            logger.error(f"LLM match analysis failed: {e}")
            return self._create_fallback_response(str(e))

    def _convert_to_legacy_format(self, llm_result: dict, profile: Dict, job: Dict) -> Dict[str, Any]:
     """Convert LLM results to backward-compatible format"""

     return {
        "overall_score": round(llm_result["overall_score"], 2),
        "section_scores": {
            "skills": round(llm_result["skills_score"]["score"], 2),
            "experience": round(llm_result["experience_score"]["score"], 2),
            "education": round(llm_result["education_score"]["score"], 2)
        },
        "missing": {
            "skills": llm_result["skills_score"]["missing_keywords"],
            "experience_keywords": llm_result["experience_score"]["missing_keywords"],
            "education_keywords": llm_result["education_score"]["missing_keywords"]
        },
        "feedback": [
            "🔍 LLM-Powered Analysis",
            "",
            "💡 Overall Assessment",
            llm_result["overall_reasoning"],
            "",
            f"🧠 Skills Match — {llm_result['skills_score']['score']}%",
            llm_result["skills_score"]["reasoning"],
            "",
            f"🛠️ Experience Match — {llm_result['experience_score']['score']}%",
            llm_result["experience_score"]["reasoning"],
            "",
            f"🎓 Education Match — {llm_result['education_score']['score']}%",
            llm_result["education_score"]["reasoning"],
            "",
            "✅ Recommendations",
            *[f"- {rec}" for rec in llm_result["recommendations"]],
            "",
            f"📈 Application Fit Prediction: {llm_result['application_probability']}"
        ],
        "llm_analysis": {
            "detailed_scores": {
                "skills": {
                    "score": llm_result["skills_score"]["score"],
                    "reasoning": llm_result["skills_score"]["reasoning"],
                    "strengths": llm_result["skills_score"]["strengths"],
                    "gaps": llm_result["skills_score"]["gaps"]
                },
                "experience": {
                    "score": llm_result["experience_score"]["score"],
                    "reasoning": llm_result["experience_score"]["reasoning"],
                    "strengths": llm_result["experience_score"]["strengths"],
                    "gaps": llm_result["experience_score"]["gaps"]
                },
                "education": {
                    "score": llm_result["education_score"]["score"],
                    "reasoning": llm_result["education_score"]["reasoning"],
                    "strengths": llm_result["education_score"]["strengths"],
                    "gaps": llm_result["education_score"]["gaps"]
                }
            },
            "recommendations": llm_result["recommendations"],
            "application_probability": llm_result["application_probability"],
            "overall_reasoning": llm_result["overall_reasoning"]
        },
        "metadata": {
            "matching_method": "llm_based",
            "model_config": self.config.__dict__,
            "analysis_version": "1.0"
        }
    }


    def _create_fallback_response(self, error_message: str) -> Dict[str, Any]:
        """Create fallback response when LLM analysis fails"""
        return {
            "overall_score": 0.0,
            "section_scores": {"skills": 0.0, "experience": 0.0, "education": 0.0},
            "missing": {"skills": [], "experience_keywords": [], "education_keywords": []},
            "feedback": [
                "ANALYSIS ERROR",
                f"LLM-based analysis failed: {error_message}",
                "Please check your profile and job data, then try again."
            ],
            "error": error_message,
            "metadata": {"matching_method": "fallback", "status": "failed"}
        }

def match_score(payload: Dict[str, Any]) -> Dict[str, Any]:
    matcher = LLMJobMatcher()
    return matcher.analyze_match({
        "profile": payload.get("profile", {}),
        "resume": payload.get("resume", ""),
        "job": payload.get("job", {})
    })

