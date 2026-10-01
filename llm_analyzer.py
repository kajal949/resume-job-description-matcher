
import requests
from prompts import SYSTEM_PROMPT, build_analysis_prompt

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"


def generate_resume_analysis(
    resume_text,
    job_description,
    match_results,
):
    prompt = build_analysis_prompt(
        resume_text=resume_text,
        job_description=job_description,
        match_results=match_results,
    )

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.2},
        },
        timeout=(10, 300),
    )

    response.raise_for_status()
    report = response.json().get("message", {}).get("content", "").strip()

    if not report:
        raise RuntimeError("Ollama returned an empty AI report.")

    return report