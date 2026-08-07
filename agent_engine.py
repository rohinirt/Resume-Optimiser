import os
import json
from google import genai
from google.genai import types 
import streamlit as st


# Fetch API Key securely
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Missing GEMINI_API_KEY. Please set it in secrets.toml or Streamlit Cloud Secrets.")
    st.stop()

# Initialize Client
client = genai.Client(api_key=api_key)

AGENT_PROMPT = """
You are an expert ATS (Applicant Tracking System) Specialist and Senior Data Analytics Hiring Manager.
Analyze the provided Master Resume, Projects, and Job Description (JD).

Perform the following:
1. Calculate Initial ATS Score (0-100), identify matching keywords, and missing keywords.
2. Evaluate Role Fitness (Strengths, Gaps, Strategy).
3. Rewrite the Resume Sections to align strictly with the JD (highlighting relevant Data Analytics tools like SQL, Python, Tableau, Power BI).
4. Calculate Updated ATS Score post-alignment.
5. Provide a standardized filename for saving (e.g., John_Doe_Data_Analyst_Google.docx).

Return ONLY a valid JSON object matching this schema:
{
  "initial_ats_score": 65,
  "matching_keywords": ["Python", "SQL"],
  "missing_keywords": ["A/B Testing", "Snowflake"],
  "fitness_summary": "Strong core skills, missing enterprise data warehousing context.",
  "suggested_rewrites": "Full updated text of the optimized resume...",
  "updated_ats_score": 92,
  "suggested_filename": "Jane_Doe_DataAnalyst_TargetCompany"
}
"""

def analyze_and_optimize_resume(master_resume, projects, jd_text):
    user_input = f"""
    --- MASTER RESUME ---
    {master_resume}

    --- ADDITIONAL PROJECTS / EXP ---
    {projects}

    --- JOB DESCRIPTION ---
    {jd_text}
    """

    max_retries = 3
    delay = 2  # seconds to wait before retrying

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=AGENT_PROMPT,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)

        except errors.APIError as e:
            # Handle 503 Server Unavailable
            if e.code == 503 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff (wait 2s, then 4s)
                continue
            else:
                raise e
