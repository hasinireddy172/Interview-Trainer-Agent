"""
╔══════════════════════════════════════════════════════════════════╗
║              INTERVIEW TRAINER AGENT — INSTRUCTIONS              ║
║  Edit the constants below to customise the agent's behaviour.    ║
╚══════════════════════════════════════════════════════════════════╝

All prompt templates use Python f-string placeholders:
  {resume_text}   — raw text extracted from the uploaded PDF
  {job_role}      — job role entered by the user
  {context}       — RAG-retrieved knowledge-base snippets (optional)

To add a new question category, duplicate one of the
QUESTIONS_* blocks, give it a unique key, and register it in
QUESTION_CATEGORIES at the bottom of this file.
"""

# ──────────────────────────────────────────────────────────────────
# AGENT PERSONA
# ──────────────────────────────────────────────────────────────────
AGENT_PERSONA = """You are an elite interview coach and career strategist with 15+ years of
experience preparing candidates for roles at Fortune 500 companies and top-tier startups.
You provide precise, actionable, and encouraging guidance tailored to each candidate's unique
background. Your tone is professional yet warm, and you always ground your answers in the
specific resume and job role provided."""

# ──────────────────────────────────────────────────────────────────
# RESUME EXTRACTION PROMPT
# ──────────────────────────────────────────────────────────────────
RESUME_EXTRACTION_PROMPT = """{persona}

Extract ALL information from the resume below. Return ONLY a valid JSON object — no markdown, no explanation.

Use exactly these keys (use empty string or empty array when a field is not present):

{{
  "name": "full name",
  "email": "email or ''",
  "phone": "phone or ''",
  "location": "city/state/country or ''",
  "linkedin": "linkedin URL or ''",
  "github": "github URL or ''",
  "website": "portfolio URL or ''",
  "summary": "2-3 sentence professional summary written by you based on the resume",
  "skills": ["every technical and soft skill mentioned"],
  "education": [
    {{
      "degree": "degree name",
      "institution": "institution name",
      "year": "year or duration",
      "gpa": "GPA if present or ''"
    }}
  ],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "duration": "start - end dates",
      "location": "city or remote",
      "responsibilities": ["key responsibility or achievement 1", "key responsibility 2"]
    }}
  ],
  "internships": [
    {{
      "title": "intern role",
      "company": "company name",
      "duration": "dates",
      "responsibilities": ["responsibility 1"]
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": "what it does",
      "technologies": ["tech1", "tech2"],
      "link": "URL or ''"
    }}
  ],
  "certifications": ["cert name — issuer — year"],
  "achievements": ["achievement 1", "achievement 2"],
  "publications": ["publication 1"],
  "languages": ["language 1", "language 2"],
  "hobbies": ["hobby 1"]
}}

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""

# ──────────────────────────────────────────────────────────────────
# HR QUESTIONS PROMPT
# ──────────────────────────────────────────────────────────────────
HR_QUESTIONS_PROMPT = """{persona}

You are preparing a candidate for the HR round of a {job_role} interview.

Candidate resume summary:
{resume_text}

{rag_context}

Generate exactly 5 HR / situational interview questions that are highly specific to this
candidate's background and the {job_role} role.

For EACH question provide:
1. The question itself
2. Why the interviewer asks it
3. A model answer (3-5 sentences) grounded in the candidate's actual resume details

Format your response as a JSON array:
[
  {{
    "question": "...",
    "why_asked": "...",
    "model_answer": "..."
  }},
  ...
]
Return ONLY the JSON array, no markdown, no extra text.
"""

# ──────────────────────────────────────────────────────────────────
# TECHNICAL QUESTIONS PROMPT
# ──────────────────────────────────────────────────────────────────
TECHNICAL_QUESTIONS_PROMPT = """{persona}

You are preparing a candidate for the Technical round of a {job_role} interview.

Candidate resume summary:
{resume_text}

{rag_context}

Generate exactly 6 technical interview questions that test the candidate's depth of knowledge
relevant to {job_role} and the skills listed on their resume.

Mix difficulty levels: 2 foundational, 2 intermediate, 2 advanced.

For EACH question provide:
1. The question itself
2. Difficulty level: Foundational | Intermediate | Advanced
3. Key concepts being tested
4. A comprehensive model answer with examples or code snippets where appropriate

Format your response as a JSON array:
[
  {{
    "question": "...",
    "difficulty": "Foundational | Intermediate | Advanced",
    "concepts": "...",
    "model_answer": "..."
  }},
  ...
]
Return ONLY the JSON array, no markdown, no extra text.
"""

# ──────────────────────────────────────────────────────────────────
# BEHAVIORAL QUESTIONS PROMPT (STAR method)
# ──────────────────────────────────────────────────────────────────
BEHAVIORAL_QUESTIONS_PROMPT = """{persona}

You are preparing a candidate for the Behavioral round of a {job_role} interview using
the STAR method (Situation, Task, Action, Result).

Candidate resume summary:
{resume_text}

{rag_context}

Generate exactly 5 behavioral questions targeting competencies critical for {job_role}.

For EACH question provide:
1. The question itself
2. The core competency being assessed
3. A model STAR answer drawn from the candidate's real experience

Format your response as a JSON array:
[
  {{
    "question": "...",
    "competency": "...",
    "model_answer": {{
      "situation": "...",
      "task": "...",
      "action": "...",
      "result": "..."
    }}
  }},
  ...
]
Return ONLY the JSON array, no markdown, no extra text.
"""

# ──────────────────────────────────────────────────────────────────
# PREPARATION TIPS PROMPT
# ──────────────────────────────────────────────────────────────────
# Kept intentionally flat and short so granite-8b-code-instruct
# reliably returns valid JSON without prose preamble.
PREPARATION_TIPS_PROMPT = """{persona}

You are creating a personalised interview preparation guide.

Candidate resume:
{resume_text}

Target role: {job_role}
{rag_context}

Return ONLY a JSON object (no markdown, no explanation) with exactly these keys:

{{
  "strengths": ["3 to 5 specific strengths from the resume relevant to {job_role}"],
  "gaps_to_address": ["2 to 3 skill or experience gaps for {job_role}"],
  "technical_tips": ["4 concrete technical topics to study for {job_role}"],
  "hr_tips": ["3 tips for the HR round of a {job_role} interview"],
  "behavioral_tips": ["3 tips for behavioral questions using STAR method"],
  "topics_to_revise": ["5 specific topics or technologies to revise"],
  "common_mistakes": ["3 common mistakes candidates make in {job_role} interviews"],
  "company_strategy": ["3 tips on researching the company and tailoring answers"],
  "questions_to_ask": ["3 smart questions to ask the interviewer"],
  "salary_tip": "one specific salary negotiation tip for {job_role}"
}}
"""

# ──────────────────────────────────────────────────────────────────
# RAG CONTEXT TEMPLATE  (injected when knowledge-base docs exist)
# ──────────────────────────────────────────────────────────────────
RAG_CONTEXT_TEMPLATE = """
Relevant interview knowledge from the uploaded reference documents:
---
{context}
---
Use the above knowledge to enrich your answers where appropriate.
"""

RAG_CONTEXT_EMPTY = ""  # used when no RAG docs are available

# ──────────────────────────────────────────────────────────────────
# QUESTION CATEGORY REGISTRY
# ──────────────────────────────────────────────────────────────────
QUESTION_CATEGORIES = {
    "hr":         {"label": "HR Questions",         "prompt_template": HR_QUESTIONS_PROMPT},
    "technical":  {"label": "Technical Questions",  "prompt_template": TECHNICAL_QUESTIONS_PROMPT},
    "behavioral": {"label": "Behavioral Questions", "prompt_template": BEHAVIORAL_QUESTIONS_PROMPT},
}

# ──────────────────────────────────────────────────────────────────
# CHUNKING SETTINGS  (for RAG document ingestion)
# ──────────────────────────────────────────────────────────────────
RAG_CHUNK_SIZE = 500          # characters per chunk
RAG_CHUNK_OVERLAP = 50        # characters of overlap between chunks
RAG_TOP_K = 4                 # how many chunks to retrieve per query

# ──────────────────────────────────────────────────────────────────
# ALLOWED FILE TYPES
# ──────────────────────────────────────────────────────────────────
ALLOWED_RESUME_EXTENSIONS = {"pdf"}
ALLOWED_KB_EXTENSIONS = {"pdf", "txt"}
