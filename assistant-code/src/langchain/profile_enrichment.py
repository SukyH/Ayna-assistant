from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from langchain.prompts import ChatPromptTemplate
from src.langchain.main import get_llm
from langchain_core.output_parsers import JsonOutputParser
import fitz  # PyMuPDF
import docx
from io import BytesIO

# Updated profile prompt with clearer instructions
profile_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert assistant for cleaning, enriching, and organizing job seeker profiles. "
     "You will receive a partially filled or noisy profile, either in JSON, messy text, or LinkedIn-style format. "
     "Your job is to return a clean, structured, professional, and enriched version ready for job applications. "
     "Apply the following rules:\n"
     "- Fix vague, disorganized, or misplaced data.\n"
     "- If a project or role appears in the wrong section, move it to the correct field.\n"
     "- Do not hallucinate values. If something is missing and cannot be inferred, leave it empty.\n"
     "- Keep descriptions concise, job-relevant, and in plain English.\n"
     "- Return ONLY valid JSON using the exact format specified.\n"
     "- DO NOT merge projects or work experience into skills or summary.\n"
     "- Group and format education, experience, projects, and licenses as arrays with their correct keys.\n"
     "- Ensure all arrays are properly formatted even if empty.\n"
     "- Do not include any text before or after the JSON response."
     
    ),
    ("human",
     """Here is a raw profile (could be messy text, LinkedIn copy, or JSON). Please return a structured enriched version using these exact fields:

REQUIRED JSON STRUCTURE:
{{
  "fullName": "string",
  "email": "string", 
  "phone": "string",
  "location": "string",
  "linkedin": "string",
  "github": "string",
  "portfolio": "string",
  "summary": "string",
  "education": [
    {{
      "school": "string",
      "degree": "string", 
      "field": "string",
      "startDate": "string",
      "endDate": "string",
      "gpa": "string"
    }}
  ],
  "experience": [
    {{
      "company": "string",
      "position": "string",
      "startDate": "string", 
      "endDate": "string",
      "description": "string"
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "techStack": "string",
      "description": "string",
      "link": "string"
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "licenses": [
    {{
      "title": "string",
      "description": "string",
      "issueDate": "string",
      "expiryDate": "string"
    }}
  ]
}}
- All string fields must be present even if empty ""


Raw Profile to enrich:
{profile_json}
""")
])