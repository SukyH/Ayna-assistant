import os
import json
import asyncio
import httpx
import pandas as pd
from typing import Dict, List
from pathlib import Path
from PyPDF2 import PdfReader
import time
import random

# === Constants ===
API_URL = "http://localhost:8000"
RESUME_DIR = "resume_testing/resumes"
ENRICHED_DIR = "resume_testing/enriched_profiles"
OUTPUT_EXCEL = "resume_testing/test_results_with_lengths.xlsx"
Path(ENRICHED_DIR).mkdir(parents=True, exist_ok=True)

# === RESUME CONTINUATION SETTINGS ===
START_FROM_RESUME = 1
MAX_RESUMES = 105

# === PERFORMANCE SETTINGS ===
MAX_CONCURRENT_REQUESTS = 1
REQUEST_DELAY = 3.0
RETRY_ATTEMPTS = 3
RETRY_DELAY = 60.0
BATCH_SIZE = 5

# === Job Descriptions ===
JOBS = [
    {
        'job_id': 'J001',
        'title': 'AI Product Manager',
        'company': 'NeuroNova Labs',
        'description': """We're looking for a forward-thinking AI Product Manager to lead cross-functional teams and bring AI-powered solutions to life.

Requirements:
• Experience managing AI/ML or data-driven products
• Strong understanding of LLMs, model deployment, and user feedback loops
• Excellent communication and stakeholder alignment skills

Responsibilities:
• Define product vision for AI features
• Prioritize roadmap and coordinate with research and engineering teams
• Continuously improve product via experimentation and analytics

Skills:
• Product strategy • LLM awareness • Agile leadership • Prompt engineering • UX collaboration""",
        'location': 'Toronto'
    },
    {
        'job_id': 'J002',
        'title': 'Creative Strategy Lead – Social Impact Campaigns',
        'company': 'RippleEffect Media',
        'description': """RippleEffect Media is seeking a Creative Strategy Lead to spearhead powerful storytelling for non-profits, sustainability orgs, and global development projects.

Requirements:
• Background in media, communications, or marketing
• Proven experience leading social campaigns or creative projects
• Strong copywriting and visual storytelling skills

Responsibilities:
• Develop creative briefs and campaign narratives
• Lead content strategy for video, social, and print
• Collaborate with designers, videographers, and cause-driven partners

Skills:
• Campaign strategy • Content creation • Adobe Suite • Social analytics • Brand voice""",
        'location': 'New York or Remote'
    }
]

# === Feature Rating Helper ===
def rate_feature(output: str) -> int:
    """Rate feature output quality based on length (1=best, 5=worst)"""
    if not output or len(output.strip()) == 0:
        return 5
    length = len(output)
    if length > 1500:
        return 1  # Very comprehensive
    elif length > 1000:
        return 2  # Good
    elif length > 500:
        return 3  # Adequate
    elif length > 100:
        return 4  # Brief but acceptable
    else:
        return 5  # Too short/empty

def evaluate_profile_enrichment(profile: dict) -> int:
    """Evaluate profile enrichment quality"""
    if not profile:
        return 5
    
    # Key fields that should be present and populated
    key_fields = ['fullName', 'email', 'skills', 'education', 'experience', 'summary']
    populated_fields = 0
    
    for field in key_fields:
        value = profile.get(field, "")
        if field in ['skills', 'education', 'experience']:
            # These should be lists with content
            if isinstance(value, list) and len(value) > 0:
                populated_fields += 1
        else:
            # These should be non-empty strings
            if isinstance(value, str) and len(value.strip()) > 0:
                populated_fields += 1
    
    # Convert to 1-5 scale (more populated = better score)
    if populated_fields >= 5:
        return 1
    elif populated_fields >= 4:
        return 2
    elif populated_fields >= 3:
        return 3
    elif populated_fields >= 2:
        return 4
    else:
        return 5

def load_existing_results() -> Dict:
    """Load existing results if they exist"""
    all_results = {job["job_id"]: [] for job in JOBS}
    
    # Try to load from existing Excel file
    if os.path.exists(OUTPUT_EXCEL):
        try:
            print(f"📂 Loading existing results from {OUTPUT_EXCEL}...")
            for job in JOBS:
                job_id = job["job_id"]
                sheet_name = f"Job_{job_id}_Results"
                try:
                    df = pd.read_excel(OUTPUT_EXCEL, sheet_name=sheet_name)
                    # Convert DataFrame back to list of dicts
                    existing_results = df.to_dict('records')
                    # Convert errors string back to list
                    for result in existing_results:
                        if 'errors' in result and isinstance(result['errors'], str):
                            result['errors'] = result['errors'].split('; ') if result['errors'] else []
                    all_results[job_id] = existing_results
                    print(f"   ✅ Loaded {len(existing_results)} results for {job_id}")
                except Exception as e:
                    print(f"   ⚠️  No existing results for {job_id}: {e}")
        except Exception as e:
            print(f"   ⚠️  Could not load existing results: {e}")
    else:
        print(f"   📝 No existing results file found, starting fresh")
    
    return all_results


async def test_single_api_endpoint_with_retry(
    client: httpx.AsyncClient, 
    endpoint: str, 
    payload: dict,
    max_retries: int = RETRY_ATTEMPTS
) -> tuple[bool, dict, str]:
    """Test a single API endpoint with retry logic and exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            # Add small random delay to prevent thundering herd
            if attempt > 0:
                delay = RETRY_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 1)
                print(f"   ⏳ Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            
            # Add request delay for rate limiting
            await asyncio.sleep(REQUEST_DELAY)
            
            print(f"   🔄 Calling {endpoint} (attempt {attempt + 1}/{max_retries})")
            start_time = time.time()
            
            response = await client.post(
                f"{API_URL}{endpoint}", 
                json=payload,
                timeout=180.0  # Increased timeout
            )
            
            response_time = time.time() - start_time
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                return True, response.json(), ""
            elif response.status_code == 429:  # Rate limit
                print(f"   ⚠️ Rate limited (429), will retry...")
                continue
            elif response.status_code >= 500:  # Server error
                print(f"   ⚠️ Server error ({response.status_code}), will retry...")
                continue
            else:
                return False, {}, f"HTTP {response.status_code}: {response.text[:200]}"
                
        except asyncio.TimeoutError:
            print(f"   ⏰ Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                return False, {}, "Request timeout after all retries"
            continue
            
        except httpx.ConnectError as e:
            print(f"   🔌 Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return False, {}, f"Connection error: {str(e)}"
            continue
            
        except Exception as e:
            print(f"   ❌ Unexpected error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return False, {}, f"Unexpected error: {str(e)}"
            continue
    
    return False, {}, f"Failed after {max_retries} attempts"

async def process_single_resume(file_path: str, resume_id: str, client: httpx.AsyncClient) -> Dict:
    """Process a single resume through the entire pipeline with better error handling"""
    
    print(f"\n🔄 Processing {resume_id}")
    print("=" * 50)
    
    # Initialize results for all jobs
    results = {}
    for job in JOBS:
        results[job['job_id']] = {
            "resume_id": resume_id,
            "job_targeted": job["job_id"],
            "generate_resume": 5,
            "generate_cover_letter": 5,
            "match_score": 0.0,
            "autofill": 5,
            "profile_enrichment": 5,
            "resume_word_count": 0,
            "resume_page_count": 1,
            "resume_output_length": 0,
            "cover_letter_length": 0,
            "overall_rating": 5.0,
            "errors": []
        }
    
    try:
        # Step 1: Extract PDF text with better error handling
        print(f"📖 Step 1: Extracting text from PDF...")
        try:
            reader = PdfReader(file_path)
            content_parts = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ''
                    content_parts.append(page_text)
                except Exception as e:
                    print(f"   ⚠️ Error extracting page {page_num + 1}: {e}")
                    continue
            
            content = "\n".join(content_parts)
            
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            for job_id in results:
                results[job_id]["errors"].append(f"PDF extraction failed: {str(e)}")
            return results
        
        if not content.strip():
            print(f"❌ Empty PDF content!")
            for job_id in results:
                results[job_id]["errors"].append("Empty PDF content")
            return results
        
        word_count = len(content.split())
        page_count = max(1, word_count // 500)
        print(f"✅ Extracted {word_count} words (~{page_count} pages)")
        
        # Update all job results with resume stats
        for job_id in results:
            results[job_id]["resume_word_count"] = word_count
            results[job_id]["resume_page_count"] = page_count
        
        # Step 2: Enrich profile with retry
        print(f"🔧 Step 2: Enriching profile...")
        success, enrich_data, error = await test_single_api_endpoint_with_retry(
            client, "/enrich-text", {"text": content[:50000]}  # Limit text length
        )
        
        if not success:
            print(f"❌ Profile enrichment failed: {error}")
            for job_id in results:
                results[job_id]["errors"].append(f"Enrichment failed: {error}")
            return results
        
        enriched_profile = enrich_data.get("enriched", {})
        enrichment_score = evaluate_profile_enrichment(enriched_profile)
        
        print(f"✅ Profile enriched (score: {enrichment_score})")
        print(f"   📊 Fields: {list(enriched_profile.keys())}")
        
        # Save enriched profile for debugging
        try:
            enriched_path = os.path.join(ENRICHED_DIR, f"{resume_id}.json")
            enriched_data = {
                "resume_id": resume_id,
                "content": content[:5000],  # Store truncated content
                "enriched_profile": enriched_profile
            }
            with open(enriched_path, "w", encoding="utf-8") as f:
                json.dump(enriched_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Couldn't save enriched profile: {e}")
        
        # Step 3: Test against each job with controlled concurrency
        for i, job in enumerate(JOBS):
            print(f"\n🎯 Step 3.{i+1}: Testing against {job['job_id']} ({job['title']})")
            
            # Update enrichment score
            results[job['job_id']]["profile_enrichment"] = enrichment_score
            
            # Create payload once
            base_payload = {
                "profile": enriched_profile,
                "job": job,
                "resume": {}
            }
            
            # Test Resume Generation
            print(f"   📝 Testing resume generation...")
            success, resume_data, error = await test_single_api_endpoint_with_retry(
                client, "/generate-resume", base_payload
            )
            
            if success:
                resume_text = resume_data.get("resume", "")
                resume_score = rate_feature(resume_text)
                resume_length = len(resume_text.split()) if resume_text else 0
                results[job['job_id']]["generate_resume"] = resume_score
                results[job['job_id']]["resume_output_length"] = resume_length
                print(f"   ✅ Resume: score {resume_score}, {resume_length} words")
            else:
                print(f"   ❌ Resume generation failed: {error}")
                results[job['job_id']]["errors"].append(f"Resume gen failed: {error}")
            
            # Test Cover Letter Generation
            print(f"   💌 Testing cover letter generation...")
            success, cl_data, error = await test_single_api_endpoint_with_retry(
                client, "/generate-coverletter", base_payload
            )
            
            if success:
                cl_text = cl_data.get("coverletter", "")
                cl_score = rate_feature(cl_text)
                cl_length = len(cl_text.split()) if cl_text else 0
                results[job['job_id']]["generate_cover_letter"] = cl_score
                results[job['job_id']]["cover_letter_length"] = cl_length
                print(f"   ✅ Cover letter: score {cl_score}, {cl_length} words")
            else:
                print(f"   ❌ Cover letter generation failed: {error}")
                results[job['job_id']]["errors"].append(f"Cover letter gen failed: {error}")
            
            # Test Match Score
            print(f"   🎯 Testing match score...")
            match_payload = {
                "profile": enriched_profile,
                "job": job
            }
            success, match_data, error = await test_single_api_endpoint_with_retry(
                client, "/match-score", match_payload
            )
            
            if success:
                score = match_data.get("score", 0.0)
                results[job['job_id']]["match_score"] = round(float(score), 2)
                print(f"   ✅ Match score: {results[job['job_id']]['match_score']}")
            else:
                print(f"   ❌ Match score failed: {error}")
                results[job['job_id']]["errors"].append(f"Match score failed: {error}")
            
            # Test Autofill
            print(f"   🔄 Testing autofill...")

            # Create form fields with proper structure
            form_fields = [
                {"field_id": "full_name", "name": "full_name", "label": "Full Name", "type": "text", "required": True},
                {"field_id": "email", "name": "email", "label": "Email Address", "type": "email", "required": True},
                {"field_id": "phone", "name": "phone", "label": "Phone Number", "type": "tel", "required": False},
                {"field_id": "skills", "name": "skills", "label": "Key Skills", "type": "textarea", "required": False},
                {"field_id": "experience_years", "name": "experience_years", "label": "Years of Experience", "type": "number", "required": False},
                {"field_id": "location", "name": "location", "label": "Current Location", "type": "text", "required": False},
                {"field_id": "linkedin", "name": "linkedin", "label": "LinkedIn Profile", "type": "url", "required": False}
            ]

            autofill_payload = {
                "profile": enriched_profile,
                "fields": form_fields
            }

            success, autofill_data, error = await test_single_api_endpoint_with_retry(
                client, "/autofill", autofill_payload
            )

            if success:
                # Count successfully filled fields
                filled_count = 0
                for field in form_fields:
                    field_id = field["field_id"]
                    value = autofill_data.get(field_id, "")
                    if value and str(value).strip():
                        filled_count += 1
                
                # Score based on how many fields were filled
                if filled_count >= 6:
                    autofill_score = 1  # Excellent
                elif filled_count >= 5:
                    autofill_score = 2  # Good
                elif filled_count >= 3:
                    autofill_score = 3  # Adequate
                elif filled_count >= 2:
                    autofill_score = 4  # Poor
                else:
                    autofill_score = 5  # Very poor
                
                results[job['job_id']]["autofill"] = autofill_score
                print(f"   ✅ Autofill: score {autofill_score}, {filled_count}/7 fields filled")
                
            else:
                print(f"   ❌ Autofill failed: {error}")
                results[job['job_id']]["errors"].append(f"Autofill failed: {error}")
            
            # Calculate overall rating
            scores = [
                results[job['job_id']]["generate_resume"],
                results[job['job_id']]["generate_cover_letter"],
                results[job['job_id']]["autofill"],
                results[job['job_id']]["profile_enrichment"]
            ]
            results[job['job_id']]["overall_rating"] = round(sum(scores) / len(scores), 2)
            
            print(f"   📊 Overall rating for {job['job_id']}: {results[job['job_id']]['overall_rating']}")
            
            # Small delay between jobs to prevent overwhelming the API
            await asyncio.sleep(0.5)
    
    except Exception as e:
        print(f"❌ Major error processing {resume_id}: {e}")
        for job_id in results:
            results[job_id]["errors"].append(f"Major error: {str(e)}")
    
    print(f"✅ Completed {resume_id}")
    return results

async def run_full_pipeline():
    """Main pipeline runner with better resource management"""
    global REQUEST_DELAY
    print(f"🚀 Starting resume testing pipeline from resume {START_FROM_RESUME}...")
    print(f"📊 Max resumes to process: {MAX_RESUMES}")
    print(f"🎛️  Performance settings:")
    print(f"   • Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    print(f"   • Request delay: {REQUEST_DELAY}s")
    print(f"   • Retry attempts: {RETRY_ATTEMPTS}")
    print(f"   • Batch size: {BATCH_SIZE}")
    
    # Check if resume directory exists
    if not os.path.exists(RESUME_DIR):
        print(f"❌ Resume directory {RESUME_DIR} not found!")
        return
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(RESUME_DIR) if f.endswith('.pdf')]
    pdf_files.sort()  # Ensure consistent ordering
    print(f"📁 Found {len(pdf_files)} total PDF files")
    
    if not pdf_files:
        print("❌ No PDF files found in resume directory!")
        return
    
    # Load existing results
    all_results = load_existing_results()
    
    # Calculate which resumes to process
    start_index = START_FROM_RESUME - 1  # Convert to 0-based index
    end_index = min(MAX_RESUMES, len(pdf_files))
    
    if start_index >= len(pdf_files):
        print(f"❌ Start resume {START_FROM_RESUME} is beyond available files ({len(pdf_files)})")
        return
    
    resumes_to_process = pdf_files[start_index:end_index]
    print(f"📋 Will process resumes {START_FROM_RESUME} to {min(start_index + len(resumes_to_process), MAX_RESUMES)}")
    print(f"📊 That's {len(resumes_to_process)} resumes to process")
    
    # Show existing progress
    existing_count = len(all_results[JOBS[0]["job_id"]]) if all_results[JOBS[0]["job_id"]] else 0
    print(f"📂 Found {existing_count} existing results")
    
    processed_count = existing_count
    
    # Configure HTTP client with better settings
    limits = httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
        keepalive_expiry=30.0
    )
    
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(180.0, connect=60.0),
        limits=limits,
        http2=False  # Disable HTTP/2 for better compatibility
    ) as client:
        
     
        
        # Process resumes in batches
        for batch_start in range(0, len(resumes_to_process), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(resumes_to_process))
            batch = resumes_to_process[batch_start:batch_end]
            
            print(f"\n📦 PROCESSING BATCH {batch_start//BATCH_SIZE + 1} ({len(batch)} resumes)")
            print("=" * 60)
            
            
            # Process each resume in the batch
            for i, filename in enumerate(batch):
                current_resume_num = START_FROM_RESUME + batch_start + i
                resume_id = f"R{current_resume_num:04d}"
                file_path = os.path.join(RESUME_DIR, filename)
                
                # Check if this resume was already processed
                already_processed = any(
                    result.get('resume_id') == resume_id 
                    for results in all_results.values() 
                    for result in results
                )
                
                if already_processed:
                    print(f"\n⏭️  SKIPPING {resume_id} ({filename}) - already processed")
                    continue
                
                print(f"\n📄 RESUME {current_resume_num}/{MAX_RESUMES}: {filename}")
                
                # Process this resume
                try:
                    resume_results = await process_single_resume(file_path, resume_id, client)
                    
                    # Add results to our collection
                    for job_id, result in resume_results.items():
                        all_results[job_id].append(result)
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to process {resume_id}: {e}")
                    # Add error result
                    for job_id in [job["job_id"] for job in JOBS]:
                        error_result = {
                            "resume_id": resume_id,
                            "job_targeted": job_id,
                            "generate_resume": 5,
                            "generate_cover_letter": 5,
                            "match_score": 0.0,
                            "autofill": 5,
                            "profile_enrichment": 5,
                            "resume_word_count": 0,
                            "resume_page_count": 1,
                            "resume_output_length": 0,
                            "cover_letter_length": 0,
                            "overall_rating": 5.0,
                            "errors": [f"Processing failed: {str(e)}"]
                        }
                        all_results[job_id].append(error_result)
                    processed_count += 1
                
                # Save interim results more frequently
                if processed_count % 5 == 0:  # Every 5 instead of 10
                    print(f"\n💾 Saving interim results after {processed_count} total resumes...")
                    try:
                        interim_file = f"resume_testing/interim_results_{processed_count}.xlsx"
                        with pd.ExcelWriter(interim_file, engine='openpyxl') as writer:
                            for job_id, results in all_results.items():
                                if results:
                                    df = pd.DataFrame(results)
                                    # Convert errors list to string for Excel
                                    if 'errors' in df.columns:
                                        df['errors'] = df['errors'].apply(lambda x: '; '.join(x) if x else '')
                                    df.to_excel(writer, sheet_name=f"Job_{job_id}_Results", index=False)
                        print(f"✅ Interim results saved to {interim_file}")
                    except Exception as e:
                        print(f"⚠️  Failed to save interim results: {e}")
            
            # Longer break between batches
            if batch_end < len(resumes_to_process):
                print(f"\n⏸️  Resting 10 seconds between batches...")
                await asyncio.sleep(10)
        
        # Show final progress summary
        print(f"\n📊 FINAL PROGRESS SUMMARY:")
        for job_id, results in all_results.items():
            if results:
                avg_rating = sum(r['overall_rating'] for r in results) / len(results)
                error_count = sum(1 for r in results if r.get('errors'))
                success_rate = (len(results) - error_count) / len(results) * 100
                print(f"   {job_id}: {len(results)} resumes, avg rating {avg_rating:.2f}, success rate {success_rate:.1f}%")

    # Final Excel report
    print(f"\n=== GENERATING FINAL REPORT ===")
    try:
        with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for job_id, results in all_results.items():
                if results:
                    df_temp = pd.DataFrame(results)
                    error_count = sum(1 for r in results if r.get('errors'))
                    summary_data.append({
                        'Job ID': job_id,
                        'Total Resumes': len(results),
                        'Resumes with Errors': error_count,
                        'Success Rate': f"{((len(results) - error_count) / len(results) * 100):.1f}%",
                        'Avg Overall Rating': round(df_temp['overall_rating'].mean(), 2),
                        'Avg Resume Generation': round(df_temp['generate_resume'].mean(), 2),
                        'Avg Cover Letter': round(df_temp['generate_cover_letter'].mean(), 2),
                        'Avg Autofill': round(df_temp['autofill'].mean(), 2),
                        'Avg Match Score': round(df_temp['match_score'].mean(), 2),
                        'Avg Profile Enrichment': round(df_temp['profile_enrichment'].mean(), 2)
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Individual job sheets
            for job_id, results in all_results.items():
                if results:
                    df = pd.DataFrame(results)
                    # Convert errors list to string for Excel
                    if 'errors' in df.columns:
                        df['errors'] = df['errors'].apply(lambda x: '; '.join(x) if x else '')
                    df.to_excel(writer, sheet_name=f"Job_{job_id}_Results", index=False)

        print(f"✅ Final report saved to: {OUTPUT_EXCEL}")
        print(f"📊 Total resumes processed: {processed_count}")
        
    except Exception as e:
        print(f"❌ Failed to generate final report: {e}")

if __name__ == "__main__":
    asyncio.run(run_full_pipeline())