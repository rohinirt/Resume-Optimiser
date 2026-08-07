#['gemini-3.6-flash','gemini-2.5-flash', 'gemini-1.5-flash']
import os
import json
import time
import streamlit as st
from google import genai
from google.genai import types, errors

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

SYSTEM_INSTRUCTION = """
You are an expert resume writer specializing in ATS optimization for Data Analytics roles.

Analyze the provided Job Description, Master Resume, and Additional Projects/Experience.

CRITICAL CONSTRAINTS:
1. Only use information present in the Master Resume or Additional Experience.
2. Never invent projects, tools, achievements, certifications, or numbers.
3. Rewrite bullet points using action verbs and the Google XYZ formula: "Accomplished [X], as measured by [Y], by doing [Z]".

OUTPUT REQUIREMENTS:
Return ONLY a valid JSON object matching this schema:
{
  "pre_optimization": {
    "ats_score": 65,
    "matching_keywords": ["SQL", "Python", "Tableau"],
    "missing_keywords": ["Snowflake", "A/B Testing", "dbt"]
  },
  "post_optimization": {
    "ats_score": 92,
    "matching_keywords": ["SQL", "Python", "Tableau", "A/B Testing", "ETL"],
    "missing_keywords": ["Snowflake", "dbt"]
  },
  "fitness_and_strategy": {
    "role_fitness_summary": "Strong technical foundation in SQL, Python, and ETL pipeline design from Uber experience. High fitness for senior/mid Data Analyst roles requiring operational analytics.",
    "gaps_and_missing_elements": "Lacks explicit enterprise data warehouse exposure like Snowflake or dbt, though strong in BigQuery.",
    "alignment_strategy": [
      "Front-load Google XYZ metrics on high-volume ETL pipelines (80K-90K daily records).",
      "Highlight cross-functional stakeholder leadership across global mega-regions.",
      "Emphasize dashboard migrations (Looker Studio to Streamlit) to align with advanced analytics requirements."
    ]
  },
  "section_2_tailored_content": {
    "professional_summary": "Detail-Oriented Data Analyst with hands-on experience at Uber driving high-impact analytics across automated ETL pipelines, interactive dashboards, and large-scale data systems. Skilled in SQL, BigQuery, Python, Looker Studio, and Streamlit to optimize operational SLAs.",
    "core_competencies": ["SQL", "BigQuery", "Python", "Tableau", "Looker Studio", "ETL Pipelines", "A/B Testing"],
    "professional_experience": [
      {
        "role_title": "Data Analytics Specialist, Uber",
        "bullets": [
          "Engineered and maintained automated ETL data pipelines using Google Sheets, Python, SQL, and BigQuery to process 80K–90K+ records daily/weekly, reducing performance tracking cycle times by 40%.",
          "Developed and deployed interactive Looker Studio dashboards integrated with Row-Level Security for Identity Operations enabling 200+ global users to self-serve insights.",
          "Rebuilt and migrated core analytics dashboards from Looker Studio to Streamlit using Cursor AI, improving dashboard load times and key metric discovery by 30%.",
          "Designed automated scorecards using Google Sheets and SQL to monitor vendor compliance and track operational SLAs across external BPO partners."
        ]
      },
      {
        "role_title": "Data Analyst Intern, TopN Analytics",
        "bullets": [
          "Accelerated reporting efficiency by 20% for 3+ stakeholder teams by building 4+ interactive Tableau and Looker Studio dashboards.",
          "Improved data accuracy by 85% by scraping and processing 1,000+ rows of real-time data using Python (BeautifulSoup, Pandas, NumPy).",
          "Increased cross-functional dashboard adoption by collaborating directly with teams to translate requirements into analytical solutions."
        ]
      }
    ],
    "projects": [
      {
        "project_title": "Retail Price Optimization",
        "bullets": [
          "Yielded a 28% average revenue increase per product by developing a Random Forest model in Python to forecast demand and price elasticity.",
          "Quantified business impact across pricing strategies by constructing an interactive price optimization simulator."
        ]
      },
      {
        "project_title": "Merchandise Sales Dashboard",
        "bullets": [
          "Analyzed 7,000+ orders to identify primary sales drivers, customer demographics, and purchasing behaviors using Tableau and MS Excel.",
          "Identified key demographic segments (70% male, average age 26, 60% positive reviews) to guide targeted marketing strategies."
        ]
      }
    ]
  },
  "suggested_filename": "Rohini_Tembhurnikar_Data_Analyst",
  "salary_benchmark": "₹12,000,000 - ₹18,000,000 / year (Glassdoor benchmark for Uber Data Analytics Specialist)",
  "clarifying_questions": []
}
"""

def analyze_and_optimize_resume(master_resume_text, projects_text, jd_text):
    user_input = f"""
    --- JOB DESCRIPTION ---
    {jd_text}

    --- MASTER RESUME ---
    {master_resume_text}

    --- ADDITIONAL PROJECTS / EXPERIENCE ---
    {projects_text}
    """

    models_to_try = ['gemini-3.6-flash','gemini-2.5-flash', 'gemini-1.5-flash']

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
            if e.code == 503:
                time.sleep(2)
                continue
            raise e

    raise Exception("Google AI servers are currently busy. Please try again.")
