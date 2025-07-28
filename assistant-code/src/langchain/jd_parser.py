from langdetect import detect
from langchain.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import PydanticOutputParser
from src.langchain.main import get_llm
from pydantic import BaseModel
import re
import os

class JobDescriptionSchema(BaseModel):
    title: str
    skills: list[str]
    experience: str
    education: str
    responsibilities: list[str]

parser = PydanticOutputParser(pydantic_object=JobDescriptionSchema)


llm = get_llm()

prompt = PromptTemplate(
    input_variables=["job_text"],
    template="""
You are a helpful assistant that extracts structured information from job descriptions.

Your job is to:
- Understand the content of the job posting
- Identify the job title, key skills, education requirements, experience requirements, and core responsibilities
- Extract specific experience requirements (years, type, level)
- Extract specific education requirements (degree level, field of study)
- Use brief, clear phrases
- Extract general requirements (e.g., certifications, language fluency, availability)
- Return JSON only, no explanations
- Limit responsibilities to core duties only
- Add requirements too

{format_instructions}

Example 1:
---
Job Description:
We're looking for a Software Engineer to develop APIs, collaborate in agile teams, and build scalable backend systems using Java and Spring Boot. Requires 3+ years experience in backend development and Bachelor's degree in Computer Science or related field. Familiarity with REST and CI/CD is essential.

Step-by-step reasoning:
- The job title is "Software Engineer"
- Skills: Java, Spring Boot, REST, CI/CD, backend development
- Experience: 3+ years backend development experience
- Education: Bachelor's degree in Computer Science or related field
- Responsibilities: API development, agile collaboration, scalable systems

JSON Output:
{{
  "title": "Software Engineer",
  "skills": ["Java", "Spring Boot", "REST", "CI/CD", "backend development"],
  "experience": "3+ years backend development experience",
  "education": "Bachelor's degree in Computer Science or related field", 
  "responsibilities": [
    "Develop APIs",
    "Collaborate in agile teams", 
    "Build scalable backend systems"
    "requirements": ["Excellent communication", "Team collaboration", "Full-time availability"
  
}}

Now analyze the following:
Job Description:
{job_text}
""",
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Step 5: Create Chain
chain: Runnable = prompt | llm | parser

# Step 6: Main Parsing Function
def parse_job_posting(jd_text: str | dict) -> dict:
    # Extract raw text from dict or convert to string
    if isinstance(jd_text, dict):
        jd_text = jd_text.get("text") or jd_text.get("raw") or ""
    elif not isinstance(jd_text, str):
        jd_text = str(jd_text)

    if not jd_text.strip():
        return {"title": "", "skills": [], "responsibilities": [], "raw": jd_text}

    # Retry logic: try 3 times if LLM parsing fails
    for _ in range(3):
        try:
            result = chain.invoke({"job_text": jd_text})
            return {
                "title": result.title,
                "skills": result.skills,
                "responsibilities": result.responsibilities,
                "raw": jd_text
            }
        except Exception as e:
            print("Retrying due to LLM parsing failure:", str(e))
            continue

    # Final fallback
    return {
        "title": "",
        "skills": [],
        "experience": "",
        "education": "",
        "responsibilities": [],
        "raw": jd_text
    }
