import os
import json
import time
import streamlit as st
from google import genai
from google.genai import types, errors

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# EXACT ORIGINAL SYSTEM INSTRUCTIONS (UNTOUCHED)
SYSTEM_INSTRUCTION = """
You are a Principal Data Analytics Hiring Manager and Elite ATS Optimization Specialist.

Your task is to conduct an exhaustive analysis of the provided Job Description (JD), Master Resume, Additional Work Experience File, and Projects File, then rewrite and optimize the resume sections to achieve maximum ATS compliance and recruiter impact.

### EXHAUSTIVE ANALYSIS & TAILORING RULES:
1. KEYWORD ANALYSIS:
   - Extract ALL hard skills, programming languages, databases, visualization tools, cloud platforms, analytical methods (e.g., A/B testing, ETL, data modeling), domain knowledge, and operational KPIs from the JD.
   - Perform a granular side-by-side keyword coverage assessment comparing the JD against the Master Resume and Experience/Project files.

2. EXPERIENCE REWRITING (Google XYZ Formula):
   - Analyze both the Master Resume and the Additional Work Experience file.
   - Align role bullet points directly with the primary responsibilities and tools requested in the JD.
   - Format bullet points strictly using: "Accomplished [X] as measured by [Y] by doing [Z]".
   - Bold key tools, metrics, and high-impact terms within bullet points for recruiter scannability.

3. PROJECT SELECTION:
   - Analyze the Projects File and Master Resume to identify the top 2-3 projects that best mirror the domain, tech stack, and analytical challenges described in the JD.
   - Rewrite project bullet points focusing on quantifiable business outcomes.

4. CATEGORIZED SKILLS GROUPING:
   - Maintain clean, grouped skill categories matching the structure of the Master Resume (e.g., "Programming & Databases", "Visualization & BI Tools", "Data Engineering & Workflows", "Core Competencies").
   - Remove obsolete or unrequested skills if space needs optimization, and explicitly list missing JD skills that the user does not possess.

5. ZERO HALLUCINATION CONSTRAINT:
   - Use ONLY facts, tools, metrics, and experiences present in the provided files. Do NOT invent companies, metrics, or certifications.

6. STRICT ONE-PAGE (A4) CONSTRAINT:
   - The rewritten resume MUST fit on exactly ONE A4 page. 
   - Keep bullet points concise, impactful, and non-redundant. Prioritize high-impact achievements.
   
OUTPUT REQUIREMENTS:
Return ONLY a valid JSON object following this exact structure:
{
  "pre_optimization": {
    "ats_score": 60,
    "matching_keywords": ["SQL", "Python", "Tableau", "Looker Studio", "BigQuery"],
    "missing_keywords": ["Snowflake", "A/B Testing", "dbt", "Data Governance", "Product Analytics"]
  },
  "post_optimization": {
    "ats_score": 95,
    "matching_keywords": ["SQL", "Python", "Tableau", "Looker Studio", "BigQuery", "ETL Pipelines", "A/B Testing", "SLA Monitoring"],
    "missing_keywords": ["Snowflake", "dbt"]
  },
  "fitness_and_strategy": {
    "role_fitness_summary": "Detailed summary of candidate fitness relative to seniority, domain, and core requirements...",
    "gaps_and_missing_elements": "Identified skill gaps or missing domain exposure...",
    "alignment_strategy": [
      "Strategic positioning point 1...",
      "Strategic positioning point 2..."
    ]
  },
  "summary_of_changes": [
    "Added missing JD technical keywords: A/B Testing, SLA Monitoring, and Data Governance across skills and experience sections.",
    "Restructured experience bullets using Google XYZ formula to emphasize high-volume data pipeline metrics.",
    "Preserved candidate contact info, education, and certifications while optimizing content density for 1 A4 page."
  ],
  "section_2_tailored_content": {
    "contact_info": {
      "name": "ROHINI TEMBHURNIKAR",
      "details": "(+91) 8010132326 | rohinitembhurnikar3@gmail.com | Hyderabad | LinkedIn | GitHub | Portfolio | Tableau"
    },
    "professional_summary": "Tailored, high-impact 2-3 sentence summary aligned with JD keywords...",
    "core_competencies_grouped": {
      "Programming & Databases": "SQL, BigQuery, Python (Pandas, NumPy)",
      "Visualization & BI Tools": "Looker Studio, Tableau, Streamlit, Power BI, Excel",
      "Data Engineering & Workflows": "Automated ETL Pipelines, Query Builder",
      "Core Competencies": "Data Modelling, Pipeline Troubleshooting, Root Cause Analysis, SLA Tracking"
    },
    "professional_experience": [
      {
        "role_title": "Data Analytics Specialist, Uber | Hyderabad, Jan 2026 – Aug 2026",
        "bullets": [
          "Engineered automated ETL data pipelines using Google Sheets, Python, SQL, and BigQuery processing 80K–90K+ records daily/weekly, reducing performance tracking cycle times by 40%.",
          "Deployed interactive Looker Studio dashboards integrated with Row-Level Security for Identity Operations enabling 200+ global users to self-serve insights."
        ]
      }
    ],
    "projects": [
      {
        "project_title": "Retail Price Optimization | Python",
        "bullets": [
          "Yielded a 28% average revenue increase per product by developing a Random Forest model in Python to forecast demand and calculate price elasticity."
        ]
      }
    ],
    "education": [
      "Master of Computer Application, SNDT University Mumbai (80%) | May 2025",
      "Bachelor Of Science, Nagpur University (75%) | June 2023"
    ],
    "certifications": [
      "Google Data Analytics Professional Certificate, Coursera | July 2023",
      "SQL: Data Reporting and Analysis, LinkedIn Learning | Oct 2022"
    ]
  },
  "suggested_filename": "Candidate_Data_Analyst_TargetCompany",
  "salary_benchmark": "Estimated market compensation benchmark with source reference",
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
            if e.code == 503 or e.code == 404:
                time.sleep(1.5)
                continue
            raise e

    raise Exception("Google AI models are currently busy or unavailable. Please try again in a few moments.")

def fetch_real_web_salary(company_name, job_title):
    """
    Uses Gemini API with Google Search Grounding to find real public salary information
    with verified source links.
    """
    if not company_name or not job_title or company_name.lower() == "targetcompany":
        return "No public salary data available for this role."

    prompt = f"""
    Search the public web for real salary data for the role of '{job_title}' at '{company_name}'.
    Check sites like Glassdoor, AmbitionBox, Indeed, or LinkedIn.
    
    If verified salary data is found, output a 1-sentence response with the exact compensation range in local currency and provide the markdown link source URL [Source Title](URL).
    If no public verified data is found, output strictly: "No public salary data available for this role."
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1
            )
        )
        return response.text.strip()
    except Exception:
        return "No public salary data available for this role."
