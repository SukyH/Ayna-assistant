from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.langchain.main import get_llm
from fastapi.responses import StreamingResponse
from weasyprint import HTML
from fastapi.responses import StreamingResponse
import io
from markdown2 import markdown
from weasyprint import HTML

def generate_pdf_from_doc(text: str, parse_sections: bool = True) -> bytes:
    lines = text.splitlines()
    html_sections = []
    current_section = ""

    resume_headers = {"summary", "skills", "work experience", "education", "certifications", "projects"}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if parse_sections and line.lower() in resume_headers:
            if current_section:
                html_sections.append(current_section)
            current_section = f"<h2>{line}</h2>"
        else:
            current_section += f"<p>{line}</p>"

    if current_section:
        html_sections.append(current_section)

    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: Arial, sans-serif;
          line-height: 1.6;
          margin: 40px;
        }}
        h1, h2 {{
          color: #333;
        }}
        pre {{
          white-space: pre-wrap;
          word-wrap: break-word;
        }}
      </style>
    </head>
    <body>
      <pre>{text}</pre>  <!-- Plain text fallback -->
    </body>
    </html>
    """
    return HTML(string=html_content).write_pdf()



def get_resume_chain(strategy='1shot'):
    llm = get_llm()

    if strategy == '1shot':
        prompt = ChatPromptTemplate.from_template("""
Instruction:
You are a senior resume expert. Generate ATS-optimized resumes. Extract job keywords, align with candidate experience, use metrics over tasks,
fill any gaps with tranferable strength. 
Output: Professional resume with Summary, Skills, Experience (with metrics), Education, and Certifications. 1-2 pages max. Be truthful - no fabrication.                                                                                                
                                                  
Example Output Style:
**Jamie Lin**
jamie.lin@email.com | (555) 123-4567 | LinkedIn | San Francisco

**Summary**
Software engineer with 5+ years building scalable backend services. Led teams, designed APIs, deployed on AWS.

**Skills**
Python | AWS | Docker | APIs | Team Leadership | Microservices

**Experience**
**FinNova Tech – Senior Engineer** (2021-Present)
- Led 4-engineer team, reduced API latency 42%
- Deployed containerized services on AWS ECS
- Mentored junior developers

**Education**
B.Sc. Computer Science – University of Washington (2018)

Now create similar resume for the given profile/job.
Now generate a similarly styled resume for:
User Profile: {profile}
Job Description: {job}
Resume: {resume}
""")

        return prompt | llm | StrOutputParser()

# Retry wrapper around the chain (call this in your route or logic)
async def generate_resume_with_retry(chain, input_data, min_lines=20, retries=1):
    best_resume = ""
    for _ in range(retries):
        try:
            output =  await chain.ainvoke(input_data)
            if output and output.count("\n") >= min_lines and "Work Experience" in output:
                return output
            if output and len(output) > len(best_resume):
                best_resume = output
        except Exception as e:
            print("Resume generation attempt failed:", str(e))
            continue
    return best_resume or "Resume generation failed after multiple attempts."

def get_resume_refinement_chain():
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
You are a resume expert. Improve this resume based on feedback and job requirements. Make targeted edits

Job Requirements: {job}
Profile: {profile}
Current Resume: {resume}
User Feedback: {feedback}

Focus on:
- Incorporating feedback suggestions
- Adding missing keywords from job posting
- Improving metrics/quantification
- Enhancing ATS compatibility
                                              
Output: Improved resume, ATS-friendly, max 2 pages.
""")
    return prompt | llm | StrOutputParser()

async def refine_resume_with_retry(chain, input_data, min_lines=20, retries=1):
    best = ""
    for _ in range(retries):
        try:
            out = await chain.ainvoke(input_data)
            if out and out.count("\n") >= min_lines and "Work Experience" in out:
                return out
            if out and len(out) > len(best):
                best = out
        except Exception: continue
    return best or "Resume refinement failed."
