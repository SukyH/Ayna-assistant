# Ayna: A Chrome-Based Intelligent Job Application Assistant

Ayna is a modular, LLM-powered Chrome extension designed to support job seekers throughout the recruitment pipeline. It streamlines profile enrichment, personalized resume and cover letter generation, semantic job matching, match scoring, and intelligent autofill on application platforms. This project is part of an academic research initiative exploring the use of large language models (LLMs) in real-world job application systems.

---

## 🔍 Key Features

- **Profile Enrichment**: Uses LLMs to complete and enhance user profiles based on resume or LinkedIn data.
- **Resume & Cover Letter Generation**: Tailors documents to specific job descriptions using contextual prompts.
- **Semantic Match Scoring**: Computes section-wise match between job descriptions and user profiles using hybrid models (SBERT + rule-based).
- **Intelligent Autofill**: Automatically fills job applications using hybrid logic (regex, ML classifier, and LLM fallback).
- **Privacy-Preserving Design**: All user data is stored locally in the browser via `IndexedDB`.

---

## 🧠 Technologies Used

- **Frontend**: React.js, Fluent UI, Vite
- **Backend**: FastAPI (Python)
- **LLM Orchestration**: LangChain
- **LLMs Used**: Mistral-7B, LLaMA 3 8B (via Together AI API)
- **NLP & ML**: SentenceTransformers (SBERT), scikit-learn
- **Web Scraping**: Playwright, BeautifulSoup
- **Document Generation**: WeasyPrint (PDF output)
- **Database**: Local IndexedDB (via idb-wrapper)
- **Dataset**: 105 anonymized real-world resumes

---

## 📁 Repository Structure

```
assistant-code/
├── src/
│   ├── components/          # React UI components
│   ├── extension/           # Chrome extension scripts
│   ├── langchain/           # FastAPI backend with LLM logic
│   ├── Database/            # IndexedDB logic (JS + Python)
│   └── themes/styles/       # Styling and theming
├── public/                  # Static assets
├── vite.config.js           # Frontend config
└── manifest.json            # Chrome extension manifest
test_results/
├── enriched_profiles/       # JSON profiles enriched by LLMs
├── *.xlsx                   # Model evaluation results
└── resume_tester.py         # End-to-end test script
```

---

## 📊 Evaluation & Results

We evaluated Ayna using 105 anonymized resumes from diverse demographic backgrounds. Two models, Mistral-7B and LLaMA 3 8B, were compared. LLaMA 3 8B demonstrated higher personalization and completeness across generated outputs.

---

## 🚀 Getting Started

### Clone and Install

```bash
git clone [REPO_URL]
cd assistant-code
npm install
```

### Run Frontend

```bash
npm run dev
```

### Run Backend (Python 3.10+)

```bash
pip install -r requirements.txt
uvicorn src.langchain.api:app --reload

```

### Load Chrome Extension

1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `dist/` folder

---

## 🧪 Testing Pipeline

To run automated tests on the full feature set:

```bash
python test_results/resume_tester.py
```

---

## 🔒 Privacy & Ethics

All profile data is handled locally using the browser’s `IndexedDB`. No external storage or user tracking is performed. All testing resumes were anonymized before processing.

---

## 📄 License

This repository is intended for academic use only. For other use cases, contact the authors post-review.

---

## 📚 Citation

If this work is used in your research, please cite:

> **Ayna: A Modular LLM-Based Assistant for Job Applications**  

