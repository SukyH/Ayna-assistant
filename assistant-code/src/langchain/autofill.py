from langchain.schema import HumanMessage
from src.langchain.main import get_llm
from src.langchain.models import AutofillRequest, ProfileData, Field
from langchain_core.output_parsers import JsonOutputParser
import logging
import re
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import asyncio
import time
from functools import lru_cache
import os
from sklearn.neighbors import NearestNeighbors
from src.langchain.train_classifier import training_data
from src.langchain.main import get_llm
embedder = SentenceTransformer('all-MiniLM-L6-v2') 

# ================== CONFIGURATION ================== #
llm = get_llm()
llm_semaphore = asyncio.Semaphore(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FIXED: Separate memory stores to prevent cross-contamination
persistent_autofill_memory = {}
field_usage_tracker = {}
MEMORY_VALIDATION = True  # Enable memory validation

class EnhancedClassifier:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.nn = None
        self.training_labels = []
        self.training_categories = []
        
    def load_training_data(self, training_data):
        self.training_labels = [item[0] for item in training_data]
        self.training_categories = [item[1] for item in training_data]
        embeddings = self.embedder.encode(self.training_labels)
        self.nn = NearestNeighbors(n_neighbors=3, metric='cosine').fit(embeddings)
    
    def predict(self, label):
        emb = self.embedder.encode([label])
        distances, indices = self.nn.kneighbors(emb)
        top_matches = [self.training_categories[i] for i in indices[0]]
        return (top_matches[0], 0.9) if len(set(top_matches)) == 1 else (max(set(top_matches), key=top_matches.count), 0.7)

clf = EnhancedClassifier()
clf.load_training_data(training_data) 

VALID_CATEGORIES = {
    'first_name', 'last_name', 'email', 'phone', 
    'current_company', 'current_title',
    'previous_company', 'previous_title',
    'education_school', 'degree', 'skills',
    'linkedin', 'website', 'github',
    'experience_years', 'summary', 'none'
}

# ================== FIELD TYPE DETECTION ================== #
def detect_field_type(label: str, field_id: str = "") -> str:
    """Enhanced field type detection with date field recognition"""
    label_lower = label.lower()
    field_id_lower = field_id.lower()
    
    # Date field detection (CRITICAL FIX)
    date_patterns = [
        r'date.*month|month.*date',
        r'startdate.*month|start.*month',
        r'enddate.*month|end.*month',  
        r'date.*year|year.*date',
        r'startdate.*year|start.*year',
        r'enddate.*year|end.*year',
        r'month.*input|year.*input'
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, field_id_lower) or re.search(pattern, label_lower):
            if 'month' in pattern:
                return 'date_month'
            elif 'year' in pattern:
                return 'date_year'
    
    # Standard field types
    if any(word in label_lower for word in ['company', 'employer', 'organization']):
        return 'company'
    elif any(word in label_lower for word in ['title', 'position', 'role', 'job']):
        return 'title' 
    elif any(word in label_lower for word in ['location', 'city', 'address']):
        return 'location'
    elif any(word in label_lower for word in ['description', 'responsibilities', 'duties']):
        return 'description'
    elif any(word in label_lower for word in ['email', 'mail']):
        return 'email'
    elif any(word in label_lower for word in ['phone', 'telephone', 'mobile']):
        return 'phone'
    elif any(word in label_lower for word in ['name']):
        return 'name'
        
    return 'unknown'

# ================== ENHANCED PROFILE CONVERSION ================== #
def convert_profile_to_user_format(profile: ProfileData) -> dict:
    """FIXED: Enhanced profile conversion with proper experience deduplication"""
    user_profile = {}
    
    # ... (basic info code remains the same)
    
    # ========== COMPLETELY REWRITTEN EXPERIENCE PROCESSING ========== #
    work_experiences = getattr(profile, 'experience', []) or getattr(profile, 'experiences', [])
    
    # Initialize experience fields
    for i in range(15):
        user_profile[f"exp_{i}_company"] = ""
        user_profile[f"exp_{i}_title"] = ""
        user_profile[f"exp_{i}_location"] = ""
        user_profile[f"exp_{i}_description"] = ""
        user_profile[f"exp_{i}_start_date"] = ""
        user_profile[f"exp_{i}_end_date"] = ""
        user_profile[f"exp_{i}_start_month"] = ""
        user_profile[f"exp_{i}_start_year"] = ""
        user_profile[f"exp_{i}_end_month"] = ""
        user_profile[f"exp_{i}_end_year"] = ""
    
    if work_experiences:
        logger.info(f"📋 Processing {len(work_experiences)} experiences")
        
        # FIXED: Better deduplication that considers dates
        unique_experiences = []
        seen_combinations = set()
        
        for i, exp in enumerate(work_experiences):
            company = exp.get("company", "").strip()
            position = exp.get("position", "").strip()
            start_date = exp.get("startDate", "").strip()
            end_date = exp.get("endDate", "").strip()
            
            if not company and not position:
                continue
            
            # FIXED: Include dates in deduplication key
            # This prevents treating same role at different times as duplicates
            combo_key = (
                company.lower(), 
                position.lower(), 
                start_date.lower(), 
                end_date.lower()
            )
            
            if combo_key in seen_combinations:
                logger.info(f"  SKIP exact duplicate: {company} - {position} ({start_date} to {end_date})")
                continue
            
            # FIXED: Also check for partial duplicates (same company/role but one has dates, other doesn't)
            partial_key = (company.lower(), position.lower())
            existing_partial = None
            for existing_exp in unique_experiences:
                existing_partial_key = (
                    existing_exp.get("company", "").lower(),
                    existing_exp.get("position", "").lower()
                )
                if existing_partial_key == partial_key:
                    existing_partial = existing_exp
                    break
            
            if existing_partial:
                # If we found a partial match, keep the one with more date information
                existing_start = existing_partial.get("startDate", "").strip()
                existing_end = existing_partial.get("endDate", "").strip()
                
                current_has_dates = bool(start_date or end_date)
                existing_has_dates = bool(existing_start or existing_end)
                
                if current_has_dates and not existing_has_dates:
                    # Replace the existing one with current (has better date info)
                    unique_experiences.remove(existing_partial)
                    logger.info(f"  REPLACE with better dates: {company} - {position}")
                elif existing_has_dates and not current_has_dates:
                    # Skip current (existing has better date info)
                    logger.info(f"  SKIP (existing has dates): {company} - {position}")
                    continue
                elif current_has_dates and existing_has_dates:
                    # Both have dates, check if they're actually different time periods
                    if (start_date != existing_start) or (end_date != existing_end):
                        logger.info(f"  KEEP (different time period): {company} - {position}")
                    else:
                        logger.info(f"  SKIP (same time period): {company} - {position}")
                        continue
                else:
                    # Neither has dates, treat as duplicate
                    logger.info(f"  SKIP (no dates): {company} - {position}")
                    continue
            
            seen_combinations.add(combo_key)
            unique_experiences.append(exp)
            logger.info(f"  KEEP unique: {company} - {position}")
        
        # FIXED: Sort experiences by end date (most recent first)
        def get_sort_date(exp):
            end_date = exp.get("endDate", "").strip().lower()
            if end_date in ['present', 'current', 'now', '']:
                return datetime.now()
            try:
                # Try to parse the date for sorting
                parsed = parse_date(end_date)
                if parsed['year'] and parsed['month']:
                    return datetime(int(parsed['year']), int(parsed['month']), 1)
                elif parsed['year']:
                    return datetime(int(parsed['year']), 12, 31)
                else:
                    return datetime.min
            except:
                return datetime.min
        
        unique_experiences.sort(key=get_sort_date, reverse=True)
        
        # Populate experience fields with proper indexing
        for i, exp in enumerate(unique_experiences[:15]):
            company = exp.get("company", "").strip()
            position = exp.get("position", "").strip()
            location = exp.get("location", "").strip()
            description = exp.get("description", "").strip()
            start_date = exp.get("startDate", "").strip()
            end_date = exp.get("endDate", "").strip()
            
            user_profile[f"exp_{i}_company"] = company
            user_profile[f"exp_{i}_title"] = position
            user_profile[f"exp_{i}_location"] = location
            user_profile[f"exp_{i}_description"] = description
            user_profile[f"exp_{i}_start_date"] = start_date
            user_profile[f"exp_{i}_end_date"] = end_date
            
            # Parse dates into components
            if start_date:
                start_parts = parse_date(start_date)
                user_profile[f"exp_{i}_start_month"] = start_parts['month']
                user_profile[f"exp_{i}_start_year"] = start_parts['year']
            
            if end_date:
                end_parts = parse_date(end_date)
                user_profile[f"exp_{i}_end_month"] = end_parts['month']
                user_profile[f"exp_{i}_end_year"] = end_parts['year']
            
            logger.info(f"  exp_{i}: {company} - {position} ({start_date} to {end_date})")
        
        # Current/Previous experience (now properly sorted)
        if len(unique_experiences) > 0:
            current_exp = unique_experiences[0]
            user_profile['current_company'] = current_exp.get("company", "").strip()
            user_profile['current_title'] = current_exp.get("position", "").strip()
        
        if len(unique_experiences) > 1:
            previous_exp = unique_experiences[1]
            user_profile['previous_company'] = previous_exp.get("company", "").strip()
            user_profile['previous_title'] = previous_exp.get("position", "").strip()
        
        user_profile['experience_years'] = str(len(unique_experiences))
    
    return user_profile


class SmartFieldMatcher:
    def __init__(self):
        self.rules = self._build_enhanced_rules()
        self.form_counters = {}
        self.field_id_to_exp = {}
        
    def rule_based_match(self, label: str, field_id: str, form_id: str = "default") -> Tuple[Optional[str], float]:
        """FIXED: Enhanced field grouping with better experience mapping"""
        normalized = self.normalize_label(label)
        field_type = detect_field_type(label, field_id)
        
        # Initialize form tracking
        if form_id not in self.form_counters:
            self.form_counters[form_id] = {
                "exp_group_mapping": {},
                "next_exp_index": 0
            }
        
        # FIXED: Better experience group extraction
        exp_group_match = re.search(r'workExperience-(\d+)', field_id)
        if exp_group_match:
            exp_group_id = int(exp_group_match.group(1))
            
            # FIXED: Map groups to sequential indices consistently
            if exp_group_id not in self.form_counters[form_id]["exp_group_mapping"]:
                seq_index = self.form_counters[form_id]["next_exp_index"]
                self.form_counters[form_id]["exp_group_mapping"][exp_group_id] = seq_index
                self.form_counters[form_id]["next_exp_index"] += 1
                logger.info(f"🔗 New experience group: workExperience-{exp_group_id} -> exp_{seq_index}")
            else:
                seq_index = self.form_counters[form_id]["exp_group_mapping"][exp_group_id]
            
            # Handle different field types for experiences
            if field_type in ['date_month', 'date_year']:
                if 'start' in field_id.lower():
                    suffix = 'start_month' if field_type == 'date_month' else 'start_year'
                elif 'end' in field_id.lower():
                    suffix = 'end_month' if field_type == 'date_month' else 'end_year'
                else:
                    return None, 0.0
                
                profile_key = f"exp_{seq_index}_{suffix}"
                logger.info(f"🗓️ Date field mapping: {field_id} -> {profile_key}")
                return profile_key, 0.95
            
            elif field_type == 'company':
                profile_key = f"exp_{seq_index}_company"
                logger.info(f"🏢 Company field: {label} -> {profile_key}")
                return profile_key, 0.9
                
            elif field_type == 'title':
                profile_key = f"exp_{seq_index}_title"
                logger.info(f"💼 Title field: {label} -> {profile_key}")
                return profile_key, 0.9
                
            elif field_type == 'location':
                profile_key = f"exp_{seq_index}_location"
                logger.info(f"📍 Location field: {label} -> {profile_key}")
                return profile_key, 0.9
                
            elif field_type == 'description':
                profile_key = f"exp_{seq_index}_description"
                logger.info(f"📝 Description field: {label} -> {profile_key}")
                return profile_key, 0.9
        
        # Handle non-experience fields
        for pattern, profile_key in self.rules.items():
            if pattern in normalized:
                logger.info(f"📋 Rule match: {label} -> {profile_key}")
                return profile_key, 0.9
        
        return None, 0.0


def parse_date(date_str: str) -> Dict[str, str]:
    """IMPROVED: More robust date parsing"""
    if not date_str:
        return {'month': '', 'year': ''}
    
    date_lower = date_str.lower().strip()
    
    # Handle "Present", "Current", "Now"
    if date_lower in ['present', 'current', 'now']:
        current_year = datetime.now().year
        current_month = datetime.now().month
        return {'month': str(current_month), 'year': str(current_year)}
    
    # Month mapping (more comprehensive)
    month_map = {
        'january': '1', 'jan': '1',
        'february': '2', 'feb': '2', 
        'march': '3', 'mar': '3',
        'april': '4', 'apr': '4',
        'may': '5',
        'june': '6', 'jun': '6',
        'july': '7', 'jul': '7',
        'august': '8', 'aug': '8',
        'september': '9', 'sep': '9', 'sept': '9',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12'
    }
    
    month = ''
    year = ''
    
    # Extract 4-digit year first
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        year = year_match.group()
    
    # Extract month name
    for month_name, month_num in month_map.items():
        if month_name in date_lower:
            month = month_num
            break
    
    # Handle numeric formats (MM/YYYY, MM-YYYY, etc.)
    if not month:
        numeric_match = re.search(r'\b(0?[1-9]|1[0-2])[-/\s]+(19|20)\d{2}\b', date_str)
        if numeric_match:
            month = str(int(numeric_match.group(1)))
            if not year:  # Only override if we haven't found year yet
                year = numeric_match.group(2) + numeric_match.group(3)[-2:]
    
    # Handle standalone month numbers
    if not month:
        month_match = re.search(r'\b(0?[1-9]|1[0-2])\b', date_str)
        if month_match and year:  # Only if we also have a year
            month = str(int(month_match.group()))
    
    return {'month': month, 'year': year}

# ================== ENHANCED FIELD MATCHING ================== #
class SmartFieldMatcher:
    def __init__(self):
        self.rules = self._build_enhanced_rules()
        self.form_counters = {}
        self.field_id_to_exp = {}  # Track which experience each field maps to
        
    def _build_enhanced_rules(self) -> Dict[str, str]:
        return {
            # Basic info
            "first name": "first_name",
            "last name": "last_name", 
            "email": "email",
            "phone": "phone",
            
            # Current work
            "current company": "current_company",
            "company": "current_company",
            "employer": "current_company",
            "current title": "current_title",
            "title": "current_title",
            "position": "current_title",
            "job title": "current_title",
            
            # Previous work  
            "previous company": "previous_company",
            "last company": "previous_company",
            "former company": "previous_company",
            "previous title": "previous_title",
            "last title": "previous_title",
            "former title": "previous_title",
            
            # Education
            "school": "education_school",
            "university": "education_school", 
            "college": "education_school",
            "degree": "degree",
            
            # Other
            "skills": "skills",
            "linkedin": "linkedin",
            "github": "github",
            "website": "website",
            "portfolio": "website",
            "summary": "summary",
        }

    def rule_based_match(self, label: str, field_id: str, form_id: str = "default") -> Tuple[Optional[str], float]:
        """COMPLETE FIX: Enhanced rule-based matching with proper field grouping"""
        normalized = self.normalize_label(label)
        field_type = detect_field_type(label, field_id)
        
        # Initialize form tracking
        if form_id not in self.form_counters:
            self.form_counters[form_id] = {
                "exp_group_mapping": {},  # Maps workExperience-X to sequential index
                "next_exp_index": 0
            }
        
        # Extract workExperience group ID
        exp_group_match = re.search(r'workExperience-(\d+)', field_id)
        if exp_group_match:
            exp_group_id = int(exp_group_match.group(1))
            
            # Map this group to sequential index if not seen before
            if exp_group_id not in self.form_counters[form_id]["exp_group_mapping"]:
                seq_index = self.form_counters[form_id]["next_exp_index"]
                self.form_counters[form_id]["exp_group_mapping"][exp_group_id] = seq_index
                self.form_counters[form_id]["next_exp_index"] += 1
            else:
                seq_index = self.form_counters[form_id]["exp_group_mapping"][exp_group_id]
            
            # Handle date fields
            if field_type in ['date_month', 'date_year']:
                if 'start' in field_id.lower():
                    if field_type == 'date_month':
                        profile_key = f"exp_{seq_index}_start_month"
                    else:
                        profile_key = f"exp_{seq_index}_start_year"
                elif 'end' in field_id.lower():
                    if field_type == 'date_month':
                        profile_key = f"exp_{seq_index}_end_month" 
                    else:
                        profile_key = f"exp_{seq_index}_end_year"
                else:
                    return None, 0.0
                
                logger.info(f"🗓️ Date field mapping: {field_id} -> {profile_key}")
                return profile_key, 0.95
            
            # Handle other experience fields
            elif field_type == 'company':
                profile_key = f"exp_{seq_index}_company"
                logger.info(f"🏢 Company field: {label} -> {profile_key}")
                return profile_key, 0.9
                
            elif field_type == 'title':
                profile_key = f"exp_{seq_index}_title"
                logger.info(f"💼 Title field: {label} -> {profile_key}")
                return profile_key, 0.9
                
            elif field_type == 'location':
                profile_key = f"exp_{seq_index}_location"
                logger.info(f"📍 Location field: {label} -> {profile_key}")
                return profile_key, 0.9
        
        # Direct rule matches for non-experience fields
        for pattern, profile_key in self.rules.items():
            if pattern in normalized:
                return profile_key, 0.9
        
        return None, 0.0

    @lru_cache(maxsize=1000)
    def normalize_label(self, label: str) -> str:
        """Clean and normalize field labels"""
        if not label:
            return ""
        
        # Remove punctuation and convert to lowercase
        label = re.sub(r'[*:()[\]{}"]', '', label.lower())
        label = re.sub(r'\s+', ' ', label).strip()
        label = re.sub(r'^(please\s+)?(enter\s+)?(your\s+)?', '', label)
        label = re.sub(r'\s*(required|\*|\(required\))', '', label)
        
        return label
# ================== MEMORY FUNCTIONS (FIXED) ================== #
def save_to_memory(label: str, value: str, field_type: str = ""):
    """FIXED: Save to memory with validation"""
    if not value or not label:
        return
        
    # Validate that we're not storing wrong data types
    if field_type == 'date_month' and not value.isdigit():
        logger.warning(f"⚠️  Invalid month value for {label}: {value}")
        return
    
    if field_type == 'date_year' and not (value.isdigit() and len(value) == 4):
        logger.warning(f"⚠️  Invalid year value for {label}: {value}")
        return
        
    # Store with field type for validation
    persistent_autofill_memory[label.lower()] = {
        "value": value,
        "field_type": field_type,
        "timestamp": datetime.now().isoformat()
    }

def get_from_memory(label: str, field_type: str = "") -> Optional[str]:
    """FIXED: Get from memory with type validation"""
    memory_entry = persistent_autofill_memory.get(label.lower(), {})
    if not memory_entry:
        return None
        
    stored_value = memory_entry.get("value")
    stored_type = memory_entry.get("field_type", "")
    
    # Validate field type matches (prevent date field contamination)
    if field_type and stored_type and field_type != stored_type:
        logger.warning(f"⚠️  Type mismatch for {label}: expected {field_type}, got {stored_type}")
        return None
        
    return stored_value

# ================== ENHANCED GET PROFILE VALUE ================== #
def get_profile_value(key: str, user_profile: dict, label: str = "") -> str:
    """Get value from profile with proper fallbacks"""
    
    # Handle full name requests
    if "full name" in label.lower() and key == "first_name":
        return f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
    
    # Direct key lookup
    value = user_profile.get(key)
    if value:
        return str(value)
    
    # Experience years fallback
    if key == "experience_years":
        count = len([v for k, v in user_profile.items() if k.startswith("exp_") and "_company" in k and v])
        return str(count)
    
    return ""

# ================== MAIN AUTOFILL FUNCTION (FIXED) ================== #
async def smart_autofill(request: AutofillRequest) -> Dict[str, str]:
    """FIXED: Smart autofill with proper field type handling"""
    logger.info(f"🔍 Processing {len(request.fields)} fields")
    start_time = time.time()
    
    user_profile = convert_profile_to_user_format(request.profile)
    results = {}
    stats = {"memory": 0, "rules": 0, "ml": 0, "llm": 0, "unmatched": 0}
    
    # Create form-specific matcher
    form_signature = "|".join([f"{f.field_id}:{f.label}" for f in request.fields])
    form_id = f"form_{hash(form_signature)}"
    matcher = SmartFieldMatcher()
    
    logger.info(f"🆔 Processing form: {form_id}")
    
    for field in request.fields:
        if not field.label:
            continue

        label = field.label.strip()
        field_id = field.field_id
        field_type = detect_field_type(label, field_id)
        
        logger.info(f"🔎 Processing field: '{label}' (ID: {field_id}, Type: {field_type})")

        # Memory check with type validation
        if (cached := get_from_memory(label, field_type)):
            results[field_id] = cached
            stats["memory"] += 1
            logger.info(f"✅ Memory hit: {label} = {cached}")
            continue

        # Rule-based matching
        profile_key, confidence = matcher.rule_based_match(label, field_id, form_id)

        if profile_key and confidence > 0.7:
            value = get_profile_value(profile_key, user_profile, label)
            if value:
                results[field_id] = value
                stats["rules"] += 1
                save_to_memory(label, value, field_type)
                logger.info(f"✅ Rule match: {label} -> {profile_key} = {value}")
                continue

        logger.info(f"❌ No match found for: {label}")

    # Process remaining fields with ML/LLM (existing logic)
    ml_fields = [f for f in request.fields if f.field_id not in results and f.label]
    if ml_fields:
        ml_results = await _process_ml_batch(ml_fields, user_profile)
        results.update(ml_results)
        stats["ml"] = len(ml_results)

    remaining_fields = [f for f in ml_fields if f.field_id not in results]
    if remaining_fields:
        llm_results = await _process_llm_batch(remaining_fields, user_profile)
        results.update(llm_results)
        stats["llm"] = len(llm_results)
    
    stats["unmatched"] = len(request.fields) - len(results)

    logger.info(f"📊 Final Stats: {stats} | Time: {time.time()-start_time:.2f}s")
    logger.info(f"📈 Successfully filled {len(results)}/{len(request.fields)} fields")
    
    return results

# ================== ML/LLM PROCESSING (UNCHANGED) ================== #
async def _process_ml_batch(fields: List[Field], profile: dict) -> Dict[str, str]:
    """Batch process fields using ML with proper embedding handling"""
    results = {}
    batch_labels = [f.label.strip() for f in fields]
    
    # Batch embed labels
    embeddings = clf.embedder.encode(batch_labels)
    distances, indices = clf.nn.kneighbors(embeddings)

    for i, field in enumerate(fields):
        try:
            top_matches = [clf.training_categories[idx] for idx in indices[i]]
            
            if len(set(top_matches)) == 1:
                profile_key = top_matches[0]
                confidence = 0.9
            else:
                profile_key = max(set(top_matches), key=top_matches.count)
                confidence = 0.7

            value = get_profile_value(profile_key, profile, field.label)
            if confidence > 0.5 and value:
                results[field.field_id] = value
                save_to_memory(field.label, value)

        except Exception as e:
            logger.warning(f"ML processing failed for '{field.label}': {str(e)}")

    return results

async def _process_llm_batch(fields: List[Field], profile: dict) -> Dict[str, str]:
    """Process remaining fields with LLM guardrails"""
    results = {}
    semaphore = asyncio.Semaphore(5)
    
    async def process_one(field):
        async with semaphore:
            try:
                label = field.label.strip()
                llm_key = await asyncio.wait_for(
                    llm_classify_label_async(label),
                    timeout=4
                )
                if llm_key != "none" and (value := get_profile_value(llm_key, profile, label)):
                    return field.field_id, value
            except Exception:
                pass
        return None
    
    tasks = [process_one(f) for f in fields]
    for completed in asyncio.as_completed(tasks):
        if (result := await completed):
            field_id, value = result
            results[field_id] = value
            # Find the field to get proper field type
            field = next((f for f in fields if f.field_id == field_id), None)
            if field:
                field_type = detect_field_type(field.label, field_id)
                save_to_memory(field.label, value, field_type)
    
    return results

async def llm_classify_label_async(label: str) -> str:
    """Timeout-protected LLM classification with caching"""
    if hasattr(llm_classify_label_async, '_cache') and label in llm_classify_label_async._cache:
        return llm_classify_label_async._cache[label]
    
    prompt = f"""
Classify this form field label into ONE of these categories:
{", ".join(VALID_CATEGORIES)}

Label: "{label}"

Instructions:
- Look for keywords like "current", "most recent" vs "previous", "last", "former"
- For work fields, distinguish between current vs previous positions  
- If unsure or no clear match, respond with "none"
- Respond with ONLY the category name

Respond ONLY with the category name or 'none':"""
    
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(llm.invoke, [HumanMessage(content=prompt)]),
            timeout=4
        )
        result = response.content.strip().lower() if response else "none"
        
        if result not in VALID_CATEGORIES:
            result = "none"
            
        # Initialize cache if not exists
        if not hasattr(llm_classify_label_async, '_cache'):
            llm_classify_label_async._cache = {}
        llm_classify_label_async._cache[label] = result
        return result
        
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"LLM classification failed for '{label}': {str(e)}")
        return "none"