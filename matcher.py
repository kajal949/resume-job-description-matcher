
import re

import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ==================================================
# 1. SKILL DICTIONARY
# ==================================================

SKILL_DICTIONARY = {
    "Python": ["python"],
    "C++": ["c++", "cpp"],
    "C": ["c programming", "programming in c"],
    "Java": ["java", "core java"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript"],
    "SQL": ["sql", "structured query language"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb"],
    "Machine Learning": ["machine learning"],
    "Deep Learning": ["deep learning"],
    "Natural Language Processing": [
        "natural language processing",
        "nlp",
    ],
    "Data Structures and Algorithms": [
        "data structures and algorithms",
        "dsa",
    ],
    "HTML": ["html"],
    "CSS": ["css"],
    "React": ["react.js", "react"],
    "Node.js": ["node.js", "nodejs"],
    "Express.js": ["express.js", "expressjs", "express"],
    "Flask": ["flask"],
    "Django": ["django"],
    "REST API": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "restful endpoints",
    ],
    "Git": ["git"],
    "GitHub": ["github", "git hub"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes"],
    "Linux": ["linux"],
    "AWS": ["aws", "amazon web services"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Communication": ["communication skills"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "Excel": ["microsoft excel", "excel"],
    "Power BI": ["power bi"],
    "Tableau": ["tableau"],
}


# ==================================================
# 2. SKILL DESCRIPTIONS FOR SEMANTIC MATCHING
# ==================================================

SKILL_DESCRIPTIONS = {
    "Python": "Programming using Python and writing Python code.",
    "SQL": "Writing SQL queries and working with relational databases.",
    "REST API": (
        "Building or integrating REST APIs, HTTP endpoints, "
        "API routes, JSON requests and responses, and backend services."
    ),
    "Git": "Using Git for source control, commits, branches, and code versioning.",
    "GitHub": "Hosting code repositories and collaborating using GitHub.",
    "JavaScript": "Developing applications using JavaScript.",
    "Node.js": "Building server-side applications using Node.js.",
    "Express.js": "Building web servers and backend APIs using Express.js.",
    "MongoDB": "Storing and querying documents in MongoDB.",
    "Machine Learning": "Training or using machine learning models.",
    "Data Analysis": "Analyzing data using programming and statistical techniques.",
    "Problem Solving": "Solving programming, algorithmic, and technical problems.",
}


# ==================================================
# 3. FIND SKILLS IN TEXT
# ==================================================

def contains_phrase(text, phrase):
    """
    Match a phrase without matching it inside unrelated words.
    For example, 'git' will not match 'digital'.
    """
    pattern = r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)"
    return bool(re.search(pattern, text.lower()))


def find_skills(text):
    """
    Return canonical skill names detected in a document.
    """
    found = []

    for skill, variations in SKILL_DICTIONARY.items():
        if any(contains_phrase(text, phrase) for phrase in variations):
            found.append(skill)

    return found


# ==================================================
# 4. SPLIT RESUME INTO EVIDENCE SENTENCES
# ==================================================

def split_sentences(text):
    """
    Split resume text into reasonably sized evidence chunks.
    """
    chunks = re.split(r"[\n.!?;•]+", text)

    return [
        re.sub(r"\s+", " ", chunk).strip()
        for chunk in chunks
        if len(chunk.strip()) > 10
    ]


def find_explicit_evidence(skill, resume_sentences):
    """
    Return a sentence that explicitly mentions a skill.
    """
    variations = SKILL_DICTIONARY.get(skill, [skill])

    for sentence in resume_sentences:
        if any(
            contains_phrase(sentence, phrase)
            for phrase in variations
        ):
            return sentence

    return None


# ==================================================
# 5. LOAD SEMANTIC MODEL
# ==================================================

@st.cache_resource
def load_embedding_model():
    """
    Load the sentence-transformer model once and reuse it.
    The model may need an internet connection on first use.
    """
    return SentenceTransformer("all-MiniLM-L6-v2")


# ==================================================
# 6. SEMANTIC EVIDENCE SEARCH
# ==================================================

def best_semantic_evidence(requirement, resume_sentences, model):
    """
    Find the resume sentence most semantically similar
    to a job requirement.
    """
    if not resume_sentences:
        return None, 0.0

    requirement_text = SKILL_DESCRIPTIONS.get(
        requirement,
        f"Practical knowledge or experience with {requirement}.",
    )

    requirement_vector = model.encode(
        [requirement_text],
        normalize_embeddings=True,
    )

    resume_vectors = model.encode(
        resume_sentences,
        normalize_embeddings=True,
    )

    scores = cosine_similarity(
        requirement_vector,
        resume_vectors,
    )[0]

    best_index = int(np.argmax(scores))

    return (
        resume_sentences[best_index],
        float(scores[best_index]),
    )


# ==================================================
# 7. COMPARE RESUME WITH JOB DESCRIPTION
# ==================================================

def compare_resume_to_job(resume_text, job_description):
    """
    Compare resume skills with job requirements.

    Explicit matches:
        The skill or one of its known variations is present.

    Semantic matches:
        A related resume sentence passes the similarity threshold.

    Preliminary score:
        Explicit match = 1 point
        Semantic match = 0.5 point
        Unmatched requirement = 0 points
    """

    resume_skills = find_skills(resume_text)
    job_skills = find_skills(job_description)

    resume_skill_set = set(resume_skills)

    matched_skills = [
        skill
        for skill in job_skills
        if skill in resume_skill_set
    ]

    direct_gaps = [
        skill
        for skill in job_skills
        if skill not in resume_skill_set
    ]

    resume_sentences = split_sentences(resume_text)

    semantic_matches = []
    missing_skills = []
    skill_evidence = []

    # Adjust this threshold only after testing against sample resumes.
    similarity_threshold = 0.40

    model = None

    # ----------------------------------------------
    # Explicit matches and supporting evidence
    # ----------------------------------------------
    for skill in matched_skills:
        evidence = find_explicit_evidence(
            skill,
            resume_sentences,
        )

        skill_evidence.append({
            "skill": skill,
            "match_type": "Explicit skill mention",
            "similarity": None,
            "evidence": evidence,
        })

    # ----------------------------------------------
    # Semantic matches for skills not explicitly found
    # ----------------------------------------------
    if direct_gaps and resume_sentences:
        model = load_embedding_model()

        for skill in direct_gaps:
            evidence, similarity = best_semantic_evidence(
                skill,
                resume_sentences,
                model,
            )

            if (
                evidence is not None
                and similarity >= similarity_threshold
            ):
                semantic_match = {
                    "skill": skill,
                    "similarity": round(similarity * 100, 1),
                    "evidence": evidence,
                }

                semantic_matches.append(semantic_match)

                skill_evidence.append({
                    "skill": skill,
                    "match_type": "Potential semantic match",
                    "similarity": round(similarity * 100, 1),
                    "evidence": evidence,
                })

            else:
                missing_skills.append(skill)

    else:
        missing_skills = direct_gaps.copy()

    # ----------------------------------------------
    # Calculate preliminary match score
    # ----------------------------------------------
    total_requirements = len(job_skills)

    if total_requirements > 0:
        score_points = (
            len(matched_skills)
            + 0.5 * len(semantic_matches)
        )

        match_score = round(
            score_points / total_requirements * 100
        )
    else:
        match_score = 0

    # ----------------------------------------------
    # Return results for app.py
    # ----------------------------------------------
    return {
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matched_skills": matched_skills,
        "semantic_matches": semantic_matches,
        "missing_skills": missing_skills,
        "skill_evidence": skill_evidence,
        "match_score": match_score,
    }