# Resume & Job Description Semantic Matcher

An NLP-based web application that compares a resume with a job description and provides a match score, matching skills, missing skills, and AI-based suggestions.

## Features

- Upload resume in PDF or DOCX format
- Extract resume text automatically
- Identify matching and missing skills
- Calculate semantic similarity using Sentence Transformers
- Generate personalized recommendations using an LLM
- Simple interactive interface using Streamlit

## Tech Stack

- Python
- Streamlit
- NLP
- Sentence Transformers
- Scikit-learn
- PyMuPDF
- python-docx
- Ollama
- Qwen 2.5 3B

## How It Works

```text
Resume + Job Description
          ↓
     Text Extraction
          ↓
     Skill Matching
          ↓
   Semantic Similarity
          ↓
      Match Score
          ↓
      LLM Analysis
          ↓
 AI Recommendations
