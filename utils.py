import os
import json
import time
import streamlit as st
from google import genai
from google.genai import types, errors

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

SYSTEM_INSTRUCTION = """
You are a Principal Data Analytics Hiring Manager and Elite ATS Optimization Specialist.

Your task is to conduct an exhaustive analysis of the provided Job Description (JD), Master Resume, Additional Work Experience File, and Projects File, then rewrite and optimize the resume sections to achieve maximum ATS compliance and recruiter impact.

### EXHAUSTIVE ANALYSIS & TAILORING RULES:

1. KEYWORD ANALYSIS:
   - Extract ALL hard skills, programming languages, databases, visualization tools, cloud platforms, analytical methods (e.g., A/B testing, ETL, data modeling), domain knowledge, and operational KPIs from the JD.
   - Perform a granular side-by-side keyword coverage assessment comparing the JD against the Master Resume and Experience/Project files.
   - Ensure precise, non-hallucinated extraction. Never invent or assume tools not present in the files.

2. EXPERIENCE REWRITING (Google XYZ Formula):
   - Format bullet points strictly using: "Accomplished [X] as measured by [Y] by doing [Z]".
   - METRIC INTEGRITY RULE: Only include numeric metrics if present in source files.
   - Use Markdown bold syntax (**text**) around key tools and metrics.

3. PROJECT SELECTION & HYPERLINKS:
   - Analyze the Projects File and Master Resume to identify top 2-3 relevant projects.
   - CRITICAL HYPERLINK RULE: Extract and preserve any project links/URLs found in the source files. Format titles with Markdown links where links exist (e.g., "[Retail Price Optimization](https://github.com/example)") so links remain clickable and underlined in outputs.

4. SECTION LAYOUT & ORDER:
   - Order of resume sections MUST strictly follow:
     1. Contact Info
     2. Professional Summary
     3. Work Experience
     4. Projects
     5. Technical Skills  <-- MUST BE DIRECTLY BELOW PROJECTS
     6. Education
     7. Certifications

5. ZERO HALLUCINATION CONSTRAINT:
   - Use ONLY facts, tools, metrics, and experiences present in the provided files.

OUTPUT REQUIREMENTS:
Return ONLY a valid JSON object following this exact structure:
{
  "pre_optimization": {
    "ats_score": 75,
    "matching_keywords": ["SQL", "Python", "Tableau", "Looker Studio", "BigQuery"],
    "partial_matches": ["PostgreSQL (candidate has general SQL experience only)"],
    "missing_keywords": ["Snowflake", "A/B Testing", "dbt"]
  },
  "post_optimization": {
    "ats_score": 95,
    "matching_keywords": ["SQL", "Python", "Tableau", "Looker Studio", "BigQuery", "ETL Pipelines", "A/B Testing"],
    "partial_matches": ["PostgreSQL (candidate has general SQL experience only)"],
    "missing_keywords": ["Snowflake", "dbt"]
  },
  "audit_categories": {
    "hard_skills": {"score": 75, "feedback": "...", "actionable_fixes": []},
    "formatting": {"score": 95, "feedback": "...", "actionable_fixes": []},
    "impact_metrics": {"score": 70, "feedback": "...", "actionable_fixes": []},
    "length_brevity": {"score": 90, "feedback": "...", "actionable_fixes": []},
    "section_completeness": {"score": 100, "feedback": "...", "actionable_fixes": []}
  },
  "fitness_and_strategy": {
    "role_fitness_summary": "...",
    "gaps_and_missing_elements": "...",
    "alignment_strategy": ["..."]
  },
  "summary_of_changes": ["..."],
  "section_2_tailored_content": {
    "contact_info": {
      "name": "ROHINI TEMBHURNIKAR",
      "details": "(+91) 8010132326 | rohinitembhurnikar3@gmail.com | Hyderabad | [LinkedIn](https://linkedin.com) | [GitHub](https://github.com) | [Portfolio](https://portfolio.com) | [Tableau](https://tableau.com)"
    },
    "professional_summary": "...",
    "professional_experience": [
      {
        "role_title": "Data Analytics Specialist, Uber | Hyderabad, Jan 2026 – Aug 2026",
        "bullets": ["..."]
      }
    ],
    "projects": [
      {
        "project_title": "[Retail Price Optimization](https://github.com/example) | Python",
        "bullets": ["..."]
      }
    ],
    "core_competencies_grouped": {
      "Programming & Databases": "SQL, BigQuery, Python (Pandas, NumPy)",
      "Visualization & BI Tools": "Looker Studio, Tableau, Streamlit, Power BI, Excel",
      "Data Engineering & Workflows": "Automated ETL Pipelines, Query Builder",
      "Core Competencies": "Data Modelling, Pipeline Troubleshooting, SLA Tracking"
    },
    "education": ["..."],
    "certifications": ["..."]
  },
  "suggested_filename": "Candidate_Data_Analyst_TargetCompany",
  "salary_benchmark": "...",
  "clarifying_questions": []
}
"""

def analyze_and_optimize_resume(master_resume_text, projects_text, experience_text, jd_text):
    user_input = f"""
    --- JOB DESCRIPTION ---
    {jd_text}

    --- MASTER RESUME ---
    {master_resume_text}

    --- ADDITIONAL WORK EXPERIENCE FILE CONTENT ---
    {experience_text}

    --- PROJECTS FILE CONTENT ---
    {projects_text}
    """

    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except errors.APIError as e:
            if e.code in (503, 404):
                time.sleep(1.5)
                continue
            raise e

    raise Exception("Google AI models are currently busy or unavailable. Please try again in a few moments.")

def fetch_real_web_salary(job_title, location):
    """
    Fetches real-time market salary data based on job title and location.
    """
    prompt = f"Provide current estimated compensation benchmarks (entry, median, high-end) for the role of '{job_title}' in '{location}'. Keep it brief and return bullet points."
    
    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except errors.APIError as e:
            if e.code in (503, 404):
                time.sleep(1)
                continue
            break
    return "Salary benchmark data is currently unavailable."
