import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sentence_transformers import SentenceTransformer
import joblib
import numpy as np

# Enhanced training data with more examples
training_data = [
    # Name fields
    ("First Name", "first_name"),
    ("Last Name", "last_name"),
    ("Full Name", "first_name"),
    ("Given Name", "first_name"),
    ("Family Name", "last_name"),
    ("Surname", "last_name"),
    ("Your Name", "first_name"),
    ("Legal First Name", "first_name"),
    ("Legal Last Name", "last_name"),
    ("Preferred Name", "first_name"),
    ("Middle Name", "first_name"),
    ("Name", "first_name"),
    
    
    # Contact Information
    ("Email", "email"),
    ("Email Address", "email"),
    ("Work Email", "email"),
    ("Personal Email", "email"),
    ("Contact Email", "email"),
    ("E-mail", "email"),
    ("Electronic Mail", "email"),
    ("Phone", "phone"),
    ("Phone Number", "phone"),
    ("Mobile", "phone"),
    ("Mobile Number", "phone"),
    ("Cell Phone", "phone"),
    ("Telephone", "phone"),
    ("Contact Number", "phone"),
    ("Home Phone", "phone"),
    ("Work Phone", "phone"),
    ("Primary Phone", "phone"),
    
    # Address fields
    ("Address", "address_line1"),
    ("Street Address", "address_line1"),
    ("Address Line 1", "address_line1"),
    ("Address Line 2", "address_line2"),
    ("Street", "address_line1"),
    ("Home Address", "address_line1"),
    ("Mailing Address", "address_line1"),
    ("Apartment", "address_line2"),
    ("Suite", "address_line2"),
    ("Unit", "address_line2"),
    ("Apt", "address_line2"),
    ("City", "city"),
    ("Town", "city"),
    ("Municipality", "city"),
    ("State", "state"),
    ("Province", "state"),
    ("Region", "state"),
    ("ZIP Code", "zip"),
    ("Postal Code", "zip"),
    ("ZIP", "zip"),
    ("Country", "country"),
    ("Nation", "country"),
    ("Location", "location"),

    
    # Work Information
    ("Company", "current_company"),
    ("Current Company", "current_company"),
    ("Employer", "current_company"),
    ("Organization", "current_company"),
    ("Current Employer", "current_company"),
    ("Company Name", "current_company"),
    ("Job Title", "current_title"),
    ("Current Title", "current_title"),
    ("Position", "current_title"),
    ("Role", "current_title"),
    ("Current Position", "current_title"),
    ("Current Role", "current_title"),
    ("Title", "current_title"),
    ("Occupation", "current_title"),
    ("Professional Title", "current_title"),
    
    # Education
    ("School", "education_school"),
    ("University", "education_school"),
    ("College", "education_school"),
    ("Institution", "education_school"),
    ("Educational Institution", "education_school"),
    ("Alma Mater", "education_school"),
    ("Degree", "degree"),
    ("Education Level", "degree"),
    ("Qualification", "degree"),
    ("Academic Degree", "degree"),
    ("Major", "degree"),
    ("Field of Study", "degree"),
    ("Specialization", "degree"),
    
    # Skills and Experience
    ("Skills", "skills"),
    ("Technical Skills", "skills"),
    ("Core Skills", "skills"),
    ("Key Skills", "skills"),
    ("Expertise", "skills"),
    ("Technologies", "skills"),
    ("Programming Languages", "skills"),
    ("Software", "skills"),
    ("Tools", "skills"),
    ("Certifications", "skills"),
    
    # Professional Links
    ("LinkedIn", "linkedin"),
    ("LinkedIn URL", "linkedin"),
    ("LinkedIn Profile", "linkedin"),
    ("Portfolio", "website"),
    ("Website", "website"),
    ("Personal Website", "website"),
    ("Portfolio URL", "website"),
    ("GitHub", "github"),
    ("GitHub Profile", "github"),
    ("GitHub URL", "github"),
    
    # Other Professional Information
    ("Summary", "summary"),
    ("Professional Summary", "summary"),
    ("About", "summary"),
    ("Bio", "summary"),
    ("Biography", "summary"),
    ("Years of Experience", "experience_years"),
    ("Experience", "experience_years"),
    ("Work Experience", "experience_years"),
    ("Professional Experience", "experience_years"),
    ("Salary Expectation", "salary_expectation"),
    ("Expected Salary", "salary_expectation"),
    ("Compensation", "salary_expectation"),
    ("Availability", "availability"),
    ("Start Date", "availability"),
    ("Available From", "availability"),
    ("Notice Period", "availability"),
    ("Work Authorization", "work_authorization"),
    ("Visa Status", "visa_status"),
    ("Citizenship", "citizenship"),
    ("Nationality", "citizenship"),
    ("Preferred Location", "preferred_location"),
    ("Location Preference", "preferred_location"),
    ("Willing to Relocate", "willing_to_relocate"),
    ("Relocation", "willing_to_relocate"),
    ("Remote Work", "remote_work"),
    ("Work from Home", "remote_work"),
    ("Cover Letter", "cover_letter"),
    ("Why are you interested", "cover_letter"),
    ("Tell us about yourself", "summary"),
    ("Motivation", "cover_letter"),
    
    # Common form variations
    ("Please enter your first name", "first_name"),
    ("What is your email address?", "email"),
    ("Your phone number", "phone"),
    ("Current company name", "current_company"),
    ("What is your current job title?", "current_title"),
    ("Where did you go to school?", "education_school"),
    ("What degree do you have?", "degree"),
    ("List your skills", "skills"),
    ("Your LinkedIn profile URL", "linkedin"),
    ("Personal website or portfolio", "website"),
    ("Tell us about your experience", "summary"),
    ("How many years of experience do you have?", "experience_years"),
    ("What is your expected salary?", "salary_expectation"),
    ("When can you start?", "availability"),
    ("Are you authorized to work?", "work_authorization"),
    ("What is your visa status?", "visa_status"),
    ("Where are you located?", "preferred_location"),
    ("Are you willing to relocate?", "willing_to_relocate"),
    ("Can you work remotely?", "remote_work"),
    ("Why do you want this job?", "cover_letter"),
    
    # Workday specific fields
    ("Legal Name - First Name", "first_name"),
    ("Legal Name - Last Name", "last_name"),
    ("Primary Email", "email"),
    ("Primary Phone", "phone"),
    ("Home Address - Address Line 1", "address_line1"),
    ("Home Address - Address Line 2", "address_line2"),
    ("Home Address - City", "city"),
    ("Home Address - State", "state"),
    ("Home Address - Postal Code", "zip"),
    ("Home Address - Country", "country"),
    ("Most Recent Employer", "current_company"),
    ("Most Recent Job Title", "current_title"),
    ("Highest Level of Education", "degree"),
    ("School Name", "education_school"),
    ("Do you have authorization to work?", "work_authorization"),
    ("Are you willing to relocate for this position?", "willing_to_relocate"),
    ("Are you open to remote work?", "remote_work"),
    ("What interests you about this role?", "cover_letter"),
    
    # Greenhouse specific fields
    ("First name", "first_name"),
    ("Last name", "last_name"),
    ("Email address", "email"),
    ("Phone number", "phone"),
    ("Current company", "current_company"),
    ("Current title", "current_title"),
    ("Resume", "none"),  # File upload field
    ("Cover letter", "cover_letter"),
    ("LinkedIn profile", "linkedin"),
    ("Website", "website"),
    ("How did you hear about this job?", "none"),
    
    # Lever specific fields
    ("Full name", "first_name"),
    ("Email", "email"),
    ("Phone", "phone"),
    ("Current company", "current_company"),
    ("Current role", "current_title"),
    ("Years of experience", "experience_years"),
    ("Why are you interested in this role?", "cover_letter"),
    
    # Common fields that shouldn't be autofilled
    ("Password", "none"),
    ("Confirm Password", "none"),
    ("Upload Resume", "none"),
    ("Upload CV", "none"),
    ("Profile Picture", "none"),
    ("Photo", "none"),
    ("Captcha", "none"),
    ("I agree to terms", "none"),
    ("Terms and Conditions", "none"),
    ("Privacy Policy", "none"),
    ("Subscribe to newsletter", "none"),
]

def train_field_classifier():
    """Train the field classification model"""
    
    # Create DataFrame
    df = pd.DataFrame(training_data, columns=['label', 'category'])
    
    # Remove 'none' category for training (we'll handle these separately)
    df = df[df['category'] != 'none']
    
    print(f"📊 Training data: {len(df)} samples")
    print(f"📊 Categories: {df['category'].nunique()}")
    print(f"📊 Category distribution:\n{df['category'].value_counts()}")
    
    # Prepare data
    texts = df['label'].tolist()
    labels = df['category'].tolist()
    
    # Load embedding model
    print("🔄 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    print("🔄 Generating embeddings...")
    X = model.encode(texts)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Train classifier
    print("🔄 Training classifier...")
    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"✅ Training completed!")
    print(f"📊 Accuracy: {accuracy:.3f}")
    print(f"📊 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save models
    print("💾 Saving models...")
    joblib.dump(clf, 'field_classifier.pkl')
    joblib.dump(model, 'embedder.pkl')
    
    # Save training data for reference
    df.to_csv('field_training_data.csv', index=False)
    
    print("✅ Models saved successfully!")
    print("✅ Training data saved to field_training_data.csv")
    
    return clf, model

def test_classifier(clf, model, test_labels):
    """Test the classifier with sample inputs"""
    print("\n🧪 Testing classifier...")
    
    for label in test_labels:
        embedding = model.encode([label])
        prediction = clf.predict(embedding)[0]
        probabilities = clf.predict_proba(embedding)[0]
        confidence = max(probabilities)
        
        print(f"'{label}' -> {prediction} (confidence: {confidence:.3f})")

if __name__ == "__main__":
    # Train the model
    clf, model = train_field_classifier()
    
    # Test with sample inputs
    test_labels = [
        "First Name",
        "Your email address",
        "Phone number",
        "Current company",
        "Job title",
        "University name",
        "Years of experience",
        "Why do you want this job?",
        "LinkedIn profile URL",
        "Upload your resume",  # Should be classified as 'none'
        "Random field name"     # Should have low confidence
    ]
    
    test_classifier(clf, model, test_labels)