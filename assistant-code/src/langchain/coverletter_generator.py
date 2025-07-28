from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.langchain.main import get_llm
def get_coverletter_chain(strategy='2shot'):
    llm = get_llm()

    if strategy == '1shot':
        prompt = ChatPromptTemplate.from_template("""
You are an expert career coach and professional writer specializing in compelling cover letters that get candidates interviews. Your task is to create a personalized, engaging cover letter that complements the resume and addresses the specific job requirements.

**Input Data:**
- User Profile: {profile}
- Job Description: {job}
- Resume: {resume}

**Chain of Thought Process:**
1. **Hook Development:** Identify the most compelling aspect of the candidate's background that aligns with the role to create an attention-grabbing opening.

2. **Value Proposition:** Determine the unique value the candidate brings and how it addresses the company's specific needs or challenges.

3. **Story Selection:** Choose 1-2 specific examples that demonstrate relevant skills and achievements, showing rather than telling.

4. **Company Connection:** Research and incorporate specific details about the company's mission, values, recent news, or industry position to show genuine interest.

5. **Call to Action:** Craft a confident, professional closing that invites further conversation.

**Output Requirements:**
- Length: 3-4 paragraphs not more then 1 page
- Tone: Professional yet personable, confident but not arrogant
- Structure: Hook → Value proposition → Specific examples → Company connection → Strong close
- Personalization: Include specific company and role details
- Complement resume: Add context and personality, don't just repeat resume content

**Template Structure:**
[Opening Hook - Why you're excited about this specific role]
[Value Proposition - What you bring to the table]
[Specific Example(s) - Concrete achievements that demonstrate fit]
[Company Connection - Why this company specifically]
[Professional Close - Call to action and next steps]

Example with Output:
  

User Profile:
Alex Carter is a seasoned marketing professional with over 8 years of experience in digital campaigns, brand strategy, and data analytics. Skilled in tools like Google Analytics, HubSpot, and Adobe Creative Suite. Holds a BA in Marketing and recently completed a certificate in Data-Driven Marketing. Successfully managed multi-channel campaigns that increased ROI and engagement.

Job Description:
We’re looking for a Digital Marketing Manager at LuminaTech, a fast-growing SaaS company. Responsibilities include leading paid and organic campaigns, optimizing conversion rates, and using data to inform strategy. Must have 5+ years of experience, strong analytics background, and familiarity with tools like Google Ads, SEMrush, and HubSpot.

Resume (if any):
Brief resume with outdated formatting, lacks metrics or tailored keywords.
                                                  
 Generated Cover Letter

Dear Hiring Manager,

As a seasoned digital marketer with a passion for data-driven growth, I was immediately excited by the opportunity to join LuminaTech as a Digital Marketing Manager. The company’s commitment to innovative SaaS solutions and its rapid scaling in the B2B tech space strongly align with both my professional background and my enthusiasm for measurable impact.

Over the past eight years, I’ve led digital campaigns that consistently delivered strong ROI—most recently increasing client revenue by 38% through paid search optimization and multi-channel strategy at Orbit Marketing Agency. My approach blends creativity with analytics: leveraging tools like Google Ads, SEMrush, and HubSpot to uncover insights, tailor messaging, and convert leads. At BrightWave Tech, I implemented marketing automation that boosted lead conversion by 27%—a result of close collaboration with sales and design teams to fine-tune user journeys.

What sets me apart is my ability to translate data into actionable growth strategies. Whether optimizing for conversions or launching new segments, I bring a balance of analytical rigor and creative storytelling. I’m also drawn to LuminaTech’s emphasis on collaborative innovation. Your recent case study on streamlining enterprise onboarding particularly resonated with me—it reflects the kind of meaningful, customer-centric work I value.

I’d welcome the chance to bring my skills and energy to your team and contribute to LuminaTech’s continued growth. Thank you for considering my application. I look forward to the possibility of discussing how I can help elevate your digital marketing efforts.

Warm regards,
Alex Carter                                                                                                                                              
                                                  
Now, analyze the provided information and create a compelling, personalized cover letter following this process.
""")
    elif strategy == '2shot':
        prompt = ChatPromptTemplate.from_template("""
Instruction:
You are a professional cover letter writer. Follow this thought process:
Identify a strong hook based on the user’s profile
Match user strengths with company needs
Include 1–2 specific examples of accomplishments
Express interest in the company’s mission
End with a confident, warm call to action
Length should be around 1 page ( around 3-4 paragraphs)                                               
Do not lie or hallucinate.      


Input:
Profile: {profile}
Job: {job}
Resume: {resume}


Output:
Structured cover letter that complements the resume and demonstrates a clear match.
Study the two sample cover letters below. Then, create a new cover letter that applies the same thought process:
Example 1:

 Profile:
 Emma Zhao is a computer science student with 3 internships in full-stack development and cloud platforms. She’s worked with AWS, React, Python, and Docker. She's passionate about accessible tech and contributed to an open-source voice-enabled navigation tool for visually impaired users.
Job Description:
 Software Engineer Intern – Accessibility Team at AccessAI
 Looking for a student passionate about inclusive design and web accessibility. Responsibilities include building React components, writing accessible HTML/CSS, and working with backend APIs (Python/Flask). Experience with WCAG and interest in open-source contributions preferred.
Resume Summary (if provided):
 Emma’s resume highlights 3 internships, skills in React, Flask, AWS, accessibility contributions, and leadership in a Women in Tech club.
Generated Cover Letter:
Dear Hiring Team at AccessAI,
As a computer science student driven by a passion for inclusive technology, I was thrilled to see your opening for a Software Engineer Intern on the Accessibility Team. The opportunity to directly contribute to a mission that aligns with both my skills and values is one I’m genuinely excited about.
During my internship at NovaTech, I built and deployed modular React components for an internal dashboard, collaborating closely with design teams to ensure clean UI and responsive layouts. I also improved backend API response times by 25% using Flask and AWS Lambda. But what truly sets me apart is my work on an open-source project—VoiceNav, a voice-activated navigation tool for visually impaired users. This experience deepened my understanding of WCAG standards and the human impact of accessible design.
I’m especially inspired by AccessAI’s dedication to making AI products usable by all. Your recent blog on accessible LLM outputs resonated with my own belief that innovation is only meaningful when it includes everyone. I’d love to contribute to that vision.
I’d be delighted to discuss how my technical experience and commitment to accessibility can support your team. Thank you for considering my application.
Warm regards,
Emma Zhao
Example 2
Input Data
 Profile:
 James Patel is a data analyst with 2 years of experience and a recent certificate in cloud data engineering. He’s skilled in SQL, Tableau, Python, and GCP. Recently worked on a project analyzing energy consumption patterns for sustainability reporting.
Job Description:
 Data Analyst – Sustainability Insights Team at GreenGrid Analytics
 Looking for a data analyst passionate about climate action and capable of working with large datasets using SQL and cloud tools (GCP preferred). Responsibilities include dashboard development, data cleaning, and presenting actionable insights to stakeholders.
Resume Summary (if provided):
 James’s resume includes energy analytics work, cloud tools (BigQuery, GCP), visualizations with Tableau, and cross-functional collaboration.
Generated Cover Letter:
Dear GreenGrid Analytics Hiring Committee,
As a data analyst who believes in the power of data to drive climate-positive decisions, I’m excited to apply for the role on your Sustainability Insights Team. GreenGrid’s mission to accelerate decarbonization through analytics strongly aligns with my background and values.
At BlueNova Consulting, I analyzed energy usage trends across 12 commercial buildings, identifying a 15% efficiency gap that informed a multi-million-dollar retrofit proposal. I built interactive Tableau dashboards and used Python scripts to automate data cleaning, reducing processing time by 40%. Most recently, I earned a Google Cloud Data Engineering certificate and applied my skills to a personal project: visualizing electric vehicle charging patterns using BigQuery and GCP Looker Studio.
I admire GreenGrid’s recent collaboration with the municipal climate lab and the public-facing emissions explorer you launched. It’s the kind of meaningful, transparent work I strive to support. My experience presenting to both technical and non-technical audiences equips me to bridge insights across teams.
I’d welcome the opportunity to contribute to GreenGrid’s data storytelling and climate initiatives. Thank you for considering my application—I look forward to the possibility of connecting.
Sincerely,
 James Patel

Now generate a similarly styled cover letter for:
User Profile: {profile}
Job Description: {job}
Resume: {resume}

""")

    return prompt | llm | StrOutputParser()

# Retry wrapper for cover letter generation
async def generate_coverletter_with_retry(chain, input_data, min_lines=10, retries=3):
    best_cover = ""
    for _ in range(retries):
        try:
            output = await chain.ainvoke(input_data)
            if output and output.count("\n") >= min_lines and "Dear" in output:
                return output
            if output and len(output) > len(best_cover):
                best_cover = output
        except Exception as e:
            print("Cover letter generation attempt failed:", str(e))
            continue
    return best_cover or "Cover letter generation failed after multiple attempts."

def get_coverletter_refinement_chain():
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
You are a professional writing expert. Refine this cover letter based on feedback while maintaining authenticity and job relevance.

Profile: {profile}
Job: {job}
Resume Context: {resume}
Current Cover Letter: {coverletter}
User Feedback: {feedback}

Improvements to focus on:
- Address specific feedback points
- Strengthen connection between experience and job requirements  
- Maintain professional yet personalized tone

Output: Polished cover letter.
""")
    return prompt | llm | StrOutputParser()

async def refine_coverletter_with_retry(chain, input_data, min_lines=10, retries=3):
    best = ""
    for _ in range(retries):
        try:
            out = await chain.ainvoke(input_data)
            if out and out.count("\n") >= min_lines:
                return out
            if out and len(out) > len(best):
                best = out
        except Exception: continue
    return best or "Cover letter refinement failed."
