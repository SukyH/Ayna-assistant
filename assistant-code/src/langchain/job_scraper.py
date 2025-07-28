import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import spacy

nlp = spacy.load("en_core_web_sm")

async def fetch_job_description(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent to avoid blocking
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        await page.goto(url, timeout=60000)
        
        # Wait a bit for dynamic content
        await asyncio.sleep(3)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.title.string.strip() if soup.title else "Untitled"
        company = extract_company_name(soup) or extract_from_meta(soup, "og:site_name") or "Unknown Company"
        text = extract_main_text(soup)
        
        # Try site-specific selectors
        try:
            if "linkedin.com" in url:
                await page.wait_for_selector("div.description__text", timeout=10000)
                text = await page.locator("div.description__text").inner_text()
            elif "myworkdayjobs.com" in url or "workday.com" in url:
                # Try multiple Workday selectors
                selectors = [
                    'div[data-automation-id="jobPostingDescription"]',
                    'div[data-automation-id="job-posting-description"]',
                    'div.css-1t92pv'
                ]
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=8000)
                        text = await page.locator(selector).inner_text()
                        break
                    except:
                        continue
            elif "greenhouse.io" in url:
                await page.wait_for_selector("div#content", timeout=10000)
                text = await page.locator("div#content").inner_text()
            elif "lever.co" in url:
                await page.wait_for_selector("div.posting-content", timeout=10000)
                text = await page.locator("div.posting-content").inner_text()
            elif "smartrecruiters.com" in url:
                await page.wait_for_selector("div.job-description", timeout=10000)
                text = await page.locator("div.job-description").inner_text()
            elif "taleo.net" in url:
                await page.wait_for_selector("div.jobdescription", timeout=10000)
                text = await page.locator("div.jobdescription").inner_text()
            elif "icims.com" in url:
                await page.wait_for_selector("div.iCIMS_JobContent", timeout=10000)
                text = await page.locator("div.iCIMS_JobContent").inner_text()
        except Exception as e:
            print(f"Selector failed, using fallback: {e}")
            # Keep the soup text as fallback
            pass
        
        await browser.close()
        
        # Clean and extract structured data
        cleaned_text = clean_text(text)
        skills, responsibilities = extract_skills_and_responsibilities(cleaned_text)
        
        return {
            "title": title,
            "company": company,
            "raw": cleaned_text,
            "skills": skills,
            "responsibilities": responsibilities
        }

def extract_main_text(soup):
    # Remove unwanted elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    candidates = [
        soup.find('div', class_=re.compile(r"(description|content|main)", re.I)),
        soup.find('article'),
        soup.find('body')
    ]
    for c in candidates:
        if c:
            return c.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)

def extract_company_name(soup):
    possible = soup.find('meta', property='og:site_name') or soup.find('meta', property='og:title')
    return possible['content'] if possible and 'content' in possible.attrs else None

def extract_from_meta(soup, meta_name):
    tag = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
    return tag['content'].strip() if tag and tag.has_attr('content') else None

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\n+', '\n', text).strip()

def extract_skills_and_responsibilities(text):
    skills = []
    responsibilities = []
    
    if not text:
        return skills, responsibilities
    
    try:
        doc = nlp(text)
        for sent in doc.sents:
            s = sent.text.lower()
            if any(k in s for k in ["responsibilit", "duties", "you will", "key tasks"]):
                responsibilities.append(sent.text.strip())
            if any(k in s for k in ["skills", "requirements", "qualifications", "must have", "experience with"]):
                skills.append(sent.text.strip())
    except Exception as e:
        print(f"NLP error: {e}")
    
    return skills[:10], responsibilities[:10]

# Test
if __name__ == "__main__":
    url = "https://canadagoose.wd3.myworkdayjobs.com/en-US/CanadaGooseCareers/job/Toronto%2C-Ontario%2C-CAN/JR-HR-Business-Partner_R15050"
    data = asyncio.run(fetch_job_description(url))
    print(data)