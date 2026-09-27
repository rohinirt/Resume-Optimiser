import os
import re
import time
import streamlit as st
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types, errors

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Kept exactly as configured: fallback chain from newest to most broadly
# available free-tier model, all on the Gemini free tier.
MODELS = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash-lite']


# ---------------------------------------------------------------------------
# Low-level call plumbing (unchanged behavior from the original engine)
# ---------------------------------------------------------------------------

def _get_status_code(error):
    """
    Defensively pull an HTTP-style status code out of an exception, regardless of
    which google-genai SDK version/exception shape raised it. Tries known attribute
    names first, then falls back to regex-matching the stringified error.
    """
    for attr in ("code", "status_code", "http_status", "status"):
        val = getattr(error, attr, None)
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
    match = re.search(r"\b(429|503|500|404)\b", str(error))
    if match:
        return int(match.group(1))
    return None

def _extract_retry_delay(error, default=2.0):
    """Pull Google's suggested retryDelay (e.g. '49s') out of the error, if present."""
    match = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", str(error))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return default

def _generate_with_fallback(models_to_try, contents, config, max_retries_per_model=1):
    """
    Try each model in order. On 429 (quota exhausted), 503 (overloaded), 500, or 404
    (model unavailable/retired), fall back to the next model in the list rather than
    failing outright. Catches broadly (not just errors.APIError) because different
    google-genai SDK versions raise different exception classes/shapes for the same
    HTTP error.
    """
    last_error = None
    for model_name in models_to_try:
        attempts = 0
        while attempts <= max_retries_per_model:
            try:
                print(f"[agent_engine] attempting model={model_name} (attempt {attempts + 1})")
                return client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
            except Exception as e:
                last_error = e
                status = _get_status_code(e)
                print(f"[agent_engine] model={model_name} failed with status={status}: {e}")
                if status in (429, 503, 500, 404):
                    if attempts < max_retries_per_model:
                        delay = _extract_retry_delay(e)
                        print(f"[agent_engine] retrying {model_name} after {delay}s")
                        time.sleep(delay)
                        attempts += 1
                        continue
                    print(f"[agent_engine] giving up on {model_name}, moving to next fallback model")
                    break
                print(f"[agent_engine] unrecognized error shape for {model_name}, trying next model anyway")
                break
    raise last_error or Exception("All configured Gemini models failed.")

def _call_structured(system_instruction, user_input, schema_cls, temperature=0.2):
    """
    One structured-output call: forces the model's response to conform to
    schema_cls (a Pydantic model) via Gemini's response_schema, instead of the
    old approach of describing the desired JSON shape only in prose. This
    removes an entire class of bugs (missing keys, renamed keys, wrong types)
    that prose-only JSON instructions are prone to.
    """
    response = _generate_with_fallback(
        MODELS,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema_cls,
            temperature=temperature,
        ),
    )
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, schema_cls):
        return parsed
    # Defensive fallback for SDK versions that don't populate .parsed.
    return schema_cls.model_validate_json(response.text)

def _friendly_error(e):
    status = _get_status_code(e)
    if status == 429:
        return Exception(
            "All available Gemini models have hit their request quota for now "
            "(free-tier daily limit reached). Please try again later, or upgrade "
            "your Google AI Studio plan for higher limits."
        )
    return Exception(f"Google AI models are currently busy or unavailable. Please try again in a few moments. (details: {e})")


# ---------------------------------------------------------------------------
# Shared hard constraints, restated once and referenced by every prompt that
# generates or scores resume content, instead of being re-explained slightly
# differently in multiple places (which risked the model treating repeated
# phrasings as separate, weaker rules rather than one non-negotiable rule).
# ---------------------------------------------------------------------------

HARD_CONSTRAINTS = """
### HARD CONSTRAINTS — highest priority, override every other instruction below if they ever conflict
1. ZERO HALLUCINATION: Use ONLY facts, tools, employers, dates, certifications, and skills that literally appear in the provided source documents. Never invent or assume anything not present there.
2. METRIC INTEGRITY: State a numeric metric (%, count, scale) only if that exact number appears in a source document for that specific achievement. If no real number exists, describe real scope/scale instead (team size, data volume, frequency, tools used) — never fabricate a percentage or figure. A bullet with no number is always preferable to a bullet with an invented one.
Every rule below is subordinate to these two constraints.
"""


# ---------------------------------------------------------------------------
# STEP 1 — JD requirement extraction (its own call: narrow, deterministic,
# low temperature). Its output becomes the single fixed checklist that BOTH
# the pre- and post-optimization scoring calls are graded against, so the
# model can no longer set and grade its own exam in one breath.
# ---------------------------------------------------------------------------

class JDRequirements(BaseModel):
    role_title: str = Field(description="Job title as stated in the JD, or the closest reasonable inference.")
    company_name: str = Field(description="Company name if the JD states one, else an empty string.")
    hard_skills: List[str] = Field(description="Programming languages, databases, and core technical skills.")
    tools_and_platforms: List[str] = Field(description="Named tools, BI/visualization platforms, cloud platforms.")
    methodologies: List[str] = Field(description="Analytical methods/processes, e.g. A/B testing, ETL, data modeling.")
    domain_keywords: List[str] = Field(description="Domain knowledge and operational KPIs relevant to the role.")
    soft_skills: List[str] = Field(description="Soft skills explicitly or clearly implied by the JD.")
    all_required_keywords: List[str] = Field(
        description="Deduplicated union of every list above, in the JD's own wording (or the most common industry "
                     "name). This becomes the fixed, authoritative checklist every later scoring step is graded "
                     "against — completeness here matters more than in any other field."
    )

SYSTEM_INSTRUCTION_JD_EXTRACTION = """
Act as a technical recruiter specializing in Data Analytics, Business Analytics, BI, SQL/Python Analyst, Reporting, and Data roles for Service & Product based companies in the Indian IT market.

Read the Job Description and extract every distinct requirement it states or clearly implies.

Rules:
1. Extract hard skills, programming languages, databases, visualization/BI tools, cloud platforms, analytical methodologies (A/B testing, ETL, data modeling, etc.), domain knowledge, operational KPIs, and soft skills as separate categories.
2. Be exhaustive — do not skip a requirement just because it appears once, in a subordinate clause, or is only implied by context (e.g. "manage large datasets" implies data-volume/scale competence).
3. Do not add a skill the JD does not state or clearly imply.
4. `all_required_keywords` must be the deduplicated union of every category above, in the JD's exact wording or the most common industry name for it. This list is later treated as ground truth for scoring, so nothing here should be dropped, merged, or renamed once produced.
"""


# ---------------------------------------------------------------------------
# STEP 2 — Calibrated ATS scoring (reused for both pre- and post-optimization,
# always against the SAME fixed checklist from Step 1, on its own low-
# temperature call so scoring reasoning isn't diluted by simultaneous
# rewriting/creative-writing goals).
# ---------------------------------------------------------------------------

class AuditCategory(BaseModel):
    score: int
    feedback: str = Field(description="Show the rubric math for this category explicitly.")
    actionable_fixes: List[str]

class AuditCategories(BaseModel):
    hard_skills: AuditCategory
    formatting: AuditCategory
    impact_metrics: AuditCategory
    length_brevity: AuditCategory
    section_completeness: AuditCategory

class ResumeScore(BaseModel):
    ats_score: int
    matching_keywords: List[str]
    partial_matches: List[str] = Field(description="Format: 'JD term (relationship to what the resume actually has)'.")
    missing_keywords: List[str]
    audit_categories: AuditCategories

SYSTEM_INSTRUCTION_SCORING = HARD_CONSTRAINTS + """
### TASK: CALIBRATED ATS SCORING (rubric-based, not impressionistic)

You are given (a) a FIXED, already-extracted checklist of JD-required keywords — treat it as ground truth, do not add to, remove from, or re-derive it — and (b) exactly one version of a resume. Score ONLY that resume against that fixed checklist.

Use this weighted rubric and show your math in each category's `feedback` field:

1. Hard Skills & Keyword Match (40 pts): For each keyword in the fixed checklist, classify it against the resume as a full match (present, exact or a clear synonym e.g. "ML"/"Machine Learning"), a partial match (a closely related but non-identical tool/tech is present — e.g. checklist wants PostgreSQL and the resume shows general SQL, or checklist wants Tableau and the resume shows Power BI — note the relationship in one line), or missing. score = 40 x (full_matches / total_checklist_keywords), with partial matches counted at half the weight of a full match.
2. Formatting & Parsability (15 pts): deduct points only for concrete structural issues you can point to (missing section headers, inconsistent date formats, non-standard section order, garbled/run-together text suggesting a parsing issue). Do not default to a high score without checking for these.
3. Impact & Metrics Density (25 pts): score based on the percentage of experience/project bullets that contain a REAL, source-verifiable metric (not fabricated). A bullet using a scope-description fallback instead of a metric earns partial credit, not full credit.
4. Length & Brevity (10 pts): score against a ~650-750 total word target and per-bullet budgets (~20-25 words/experience bullet, ~15-25 words/project bullet, ~40-50 words/summary) treated as soft guidance, not a hard cutoff.
5. Section Completeness (10 pts): score based only on the presence of contact info, education, and certifications — do not infer completeness from anything else.

Sum the five category scores for the final `ats_score`. Calculate this identically regardless of which resume version you were given. Do not adjust the score to hit a target range — report exactly what the rubric produces, even if this resume scores unexpectedly high or low.
"""


# ---------------------------------------------------------------------------
# STEP 3 — Resume rewriting. Its own call, its own (moderate) temperature,
# doing only the creative-writing/restructuring job — not scoring itself.
# core_competencies_grouped is modeled as a list of {category, skills} pairs
# (rather than an open-ended dict) so it fits a fixed response_schema; the
# pipeline converts it back to the dict shape the rest of the app expects.
# ---------------------------------------------------------------------------

class ContactInfo(BaseModel):
    name: str
    details: str = Field(description="Plain, pipe-separated label text exactly as in the Master Resume header, e.g. '(+91) 8010132326 | name@email.com | Hyderabad | LinkedIn | GitHub'. NEVER append a URL here.")

class SkillGroup(BaseModel):
    category: str
    skills: str

class ExperienceRole(BaseModel):
    role_title: str
    bullets: List[str]

class ProjectEntry(BaseModel):
    project_title: str
    project_link: str = Field(description="Verbatim URL from the source files for this exact project, or empty string if none exists. Never invent, guess, or reuse a URL from a different project.")
    project_link_label: str = Field(description="Original link text from the source, e.g. 'Link', 'GitHub', 'Dashboard'. Empty string if project_link is empty.")
    bullets: List[str]

class FitnessStrategy(BaseModel):
    role_fitness_summary: str
    gaps_and_missing_elements: str
    alignment_strategy: List[str] = Field(description="3 concise strategic positioning points.")

class ResumeRewrite(BaseModel):
    contact_info: ContactInfo
    professional_summary: str
    core_competencies_grouped: List[SkillGroup]
    professional_experience: List[ExperienceRole]
    projects: List[ProjectEntry]
    education: List[str]
    certifications: List[str]
    suggested_filename: str = Field(description="Format: Candidate_Role_Company (use role/company from the JD requirements checklist).")
    fitness_and_strategy: FitnessStrategy
    summary_of_changes: List[str] = Field(description="3-5 bullets describing what changed and why.")

SYSTEM_INSTRUCTION_REWRITE = HARD_CONSTRAINTS + """
### TASK: RESUME REWRITING

Act as an experienced resume strategist specializing in Data Analytics, Business Analytics, BI, SQL/Python Analyst, Reporting, and Data roles for Service & Product based companies in the Indian IT market. You are given the Job Description, a FIXED JD-requirements checklist (extracted separately — treat it as authoritative, do not re-derive it), the Master Resume, an Additional Work Experience file, and a Projects file. Rewrite the resume sections below to maximize alignment with the checklist, honoring the HARD CONSTRAINTS above at all times.

1. PROFESSIONAL SUMMARY
   - Position the candidate according to the actual requirements of the JD; mention only JD-relevant technical areas.
   - ~40-50 words (soft target — prioritize honesty and coverage over hitting the count exactly).
   - Include mandatory JD hard skills naturally; avoid fluff or generic adjectives.
   - Add only experience/skills the candidate actually has, per the HARD CONSTRAINTS.
   - CALIBRATION EXAMPLE (for tone/pattern only — do not copy any content into your output):
     - Good: "Data Analyst experienced in **SQL** and **Python**, building **ETL pipelines** and **Power BI** dashboards for operations teams; skilled in root-cause analysis and stakeholder reporting." (grounded, keyword-rich, no invented claim)
     - Bad: "Highly motivated professional with 5+ years of experience driving business value." (invents years of experience nowhere in the source, generic fluff, no real keywords)

2. EXPERIENCE REWRITING (Google XYZ Formula)
   - Analyze both the Master Resume bullets and the Additional Work Experience file. Align bullets with the primary responsibilities and tools requested in the JD.
   - Format strictly as: "Accomplished [X] as measured by [Y] by doing [Z]." Start with a strong action verb, integrate mandatory JD hard skills naturally, use exact JD keywords wherever truthful, maintain clarity and business impact.
   - Include a numeric metric [Y] only when a real number/percentage/scale exists in the source for that achievement (METRIC INTEGRITY above); otherwise describe real scope/scale instead.
   - Use Markdown bold syntax (**text**) around key tools, metrics, and high-impact terms for recruiter scannability. Use no other markup.
   - ~20-25 words per bullet (soft target). Include as many bullets per role as needed to cover the JD's required skills/responsibilities — generally matching how many bullets that role has in the Master Resume (typically 3-5); only trim below the source count if truly redundant or irrelevant to the JD.
   - CALIBRATION EXAMPLE (for tone/pattern only):
     - Good (real metric in source): "Automated **ETL pipelines** in **Python** and **SQL**, cutting manual reporting time by **40%** across 3 regional teams."
     - Good (no real metric in source — uses the scope fallback): "Built **Power BI** dashboards tracking daily inventory across **12 retail locations** for the operations team."
     - Bad (invented metric not in source): "Improved team efficiency by 35%." — never produce this pattern when no source number supports it.

3. PROJECT SELECTION
   - From the Projects File and Master Resume, identify the top 2 projects that best mirror the domain, tech stack, and analytical challenges in the JD.
   - Rewrite project bullets for quantifiable business outcomes, following the same METRIC INTEGRITY rule. 2-3 bullets per project, ~15-25 words each.
   - LINK INTEGRITY: source files show hyperlink URLs inline in parentheses right after their link text (e.g. "Link (https://github.com/...)"). For each selected project, if such a URL exists for that exact project, copy it VERBATIM into `project_link` and set `project_link_label` to the original link text. If no URL exists for a chosen project, leave `project_link` as an empty string — never invent, guess, or reuse a URL from a different project.

4. CATEGORIZED SKILLS GROUPING
   - Group skills into clean categories matching the Master Resume's structure (e.g. "Programming & Databases", "Visualization & BI Tools", "Data Engineering & Workflows", "Core Competencies"), returned as a list of {category, skills} pairs.
   - Remove obsolete/unrequested skills if space needs optimizing.

5. CONTACT LINE FORMAT
   - `contact_info.details` must contain ONLY plain, pipe-separated label text exactly as it appears in the Master Resume header. Never append the parenthetical URL shown next to a link label (e.g. never output "LinkedIn (https://...)") — the application attaches the real hyperlink automatically. The only place a URL should ever appear in your output is `project_link`.

6. ONE-PAGE (A4) LENGTH TARGET
   - Aim for ~650-750 total words across all sections as a soft target — content completeness and JD-coverage take priority over hitting an exact word count. If genuinely over one page, prioritize the highest-impact, most JD-relevant bullets when trimming, and shorten wording before cutting whole bullets.

7. Also produce: `fitness_and_strategy` (role_fitness_summary, gaps_and_missing_elements distinguishing full gaps from partial matches, and a 3-point alignment_strategy roadmap), `suggested_filename` (Candidate_Role_Company, using the role/company from the JD requirements checklist), and `summary_of_changes` (3-5 bullets on what changed and why).
"""


# ---------------------------------------------------------------------------
# Deterministic, lightweight post-processing guard: LLMs are unreliable at
# hitting an exact word count, so the prompt above states soft targets and
# this only intervenes when a line is drastically over budget, rather than
# silently truncating well-formed output that's merely a few words long.
# ---------------------------------------------------------------------------

def _soft_word_guard(text, target_max_words, hard_multiplier=1.6):
    if not text:
        return text
    words = text.split()
    hard_cap = int(target_max_words * hard_multiplier)
    if len(words) > hard_cap:
        return " ".join(words[:hard_cap]).rstrip(",.;:") + "."
    return text

def _flatten_rewrite_for_scoring(rewrite: "ResumeRewrite") -> str:
    """Renders the structured rewrite back into plain text so the scoring
    call can grade the post-optimization resume the same way it grades the
    plain-text original — against the same fixed keyword checklist."""
    lines = [rewrite.contact_info.name, rewrite.contact_info.details, "",
              "PROFESSIONAL SUMMARY", rewrite.professional_summary, "", "SKILLS"]
    for g in rewrite.core_competencies_grouped:
        lines.append(f"{g.category}: {g.skills}")
    lines += ["", "EXPERIENCE"]
    for role in rewrite.professional_experience:
        lines.append(role.role_title)
        lines += [f"- {b}" for b in role.bullets]
    lines += ["", "PROJECTS"]
    for proj in rewrite.projects:
        lines.append(proj.project_title)
        lines += [f"- {b}" for b in proj.bullets]
    lines += ["", "EDUCATION"] + list(rewrite.education)
    lines += ["", "CERTIFICATIONS"] + list(rewrite.certifications)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline: 4 focused calls instead of 1 mega-call, cached end-to-end so
# re-running the app (navigating pages, an accidental double-click, Streamlit
# re-executing the script) with the same inputs never re-spends API quota.
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600, max_entries=50)
def analyze_and_optimize_resume(master_resume_text, projects_text, experience_text, jd_text):
    try:
        # Step 1: extract a fixed, reusable JD requirements checklist.
        jd_requirements = _call_structured(
            SYSTEM_INSTRUCTION_JD_EXTRACTION, jd_text, JDRequirements, temperature=0.1
        )
        jd_req_json = jd_requirements.model_dump_json(indent=2)

        # Step 2: score the ORIGINAL resume against that fixed checklist.
        pre_score = _call_structured(
            SYSTEM_INSTRUCTION_SCORING,
            f"--- FIXED JD REQUIREMENTS CHECKLIST ---\n{jd_req_json}\n\n"
            f"--- RESUME TO SCORE (ORIGINAL / PRE-OPTIMIZATION) ---\n{master_resume_text}",
            ResumeScore, temperature=0.1,
        )

        # Step 3: rewrite the resume content (its own, moderately creative call).
        rewrite_user_input = f"""
        --- JOB DESCRIPTION ---
        {jd_text}

        --- FIXED JD REQUIREMENTS CHECKLIST (extracted separately — authoritative) ---
        {jd_req_json}

        --- MASTER RESUME ---
        {master_resume_text}

        --- ADDITIONAL WORK EXPERIENCE FILE CONTENT ---
        {experience_text}

        --- PROJECTS FILE CONTENT ---
        {projects_text}
        """
        rewrite = _call_structured(
            SYSTEM_INSTRUCTION_REWRITE, rewrite_user_input, ResumeRewrite, temperature=0.4
        )

        # Step 4: score the REWRITTEN resume against the SAME fixed checklist.
        post_resume_text = _flatten_rewrite_for_scoring(rewrite)
        post_score = _call_structured(
            SYSTEM_INSTRUCTION_SCORING,
            f"--- FIXED JD REQUIREMENTS CHECKLIST ---\n{jd_req_json}\n\n"
            f"--- RESUME TO SCORE (REWRITTEN / POST-OPTIMIZATION) ---\n{post_resume_text}",
            ResumeScore, temperature=0.1,
        )

    except Exception as e:
        raise _friendly_error(e)

    return {
        "pre_optimization": pre_score.model_dump(exclude={"audit_categories"}),
        "post_optimization": post_score.model_dump(exclude={"audit_categories"}),
        "pre_audit_categories": pre_score.audit_categories.model_dump(),
        "audit_categories": post_score.audit_categories.model_dump(),
        "fitness_and_strategy": rewrite.fitness_and_strategy.model_dump(),
        "summary_of_changes": rewrite.summary_of_changes,
        "section_2_tailored_content": {
            "contact_info": rewrite.contact_info.model_dump(),
            "professional_summary": _soft_word_guard(rewrite.professional_summary, 50),
            "core_competencies_grouped": {g.category: g.skills for g in rewrite.core_competencies_grouped},
            "professional_experience": [
                {"role_title": r.role_title, "bullets": [_soft_word_guard(b, 25) for b in r.bullets]}
                for r in rewrite.professional_experience
            ],
            "projects": [
                {**p.model_dump(), "bullets": [_soft_word_guard(b, 25) for b in p.bullets]}
                for p in rewrite.projects
            ],
            "education": rewrite.education,
            "certifications": rewrite.certifications,
        },
        "suggested_filename": rewrite.suggested_filename,
    }


# ---------------------------------------------------------------------------
# Outreach templates (new): LinkedIn referral-request message + application
# email, each its own small, cheap, cached call grounded only in the JD and
# the already-verified professional_summary (never re-deriving candidate
# facts), so neither can invent skills/experience.
# ---------------------------------------------------------------------------

class ReferralTemplate(BaseModel):
    message: str = Field(description="100-150 word LinkedIn referral-request message, plain text, no markdown.")

SYSTEM_INSTRUCTION_REFERRAL = """
Act as a career coach writing a LinkedIn message on behalf of a job candidate, asking a connection to refer them for a role or share their resume internally.

Rules:
1. Tone: {tone}. Adjust word choice and formality to match this tone while staying appropriate for a professional LinkedIn message.
2. Length: strictly 100 to 150 words.
3. Reference the specific role title (from the JD) and 2-3 concrete, JD-relevant skills — draw skills ONLY from the candidate's professional summary provided below, never invent skills or experience not present there.
4. Use placeholders in [square brackets] for anything unknowable here: [Connection's Name], [Your Name], and the company name if the JD doesn't state one.
5. End with a clear, low-friction, non-pushy ask.
6. Output plain text only — no markdown formatting, no subject line.
"""

@st.cache_data(show_spinner=False, ttl=3600, max_entries=50)
def generate_referral_template(jd_text, candidate_summary, tone="Professional"):
    if not jd_text or not candidate_summary:
        return ""
    user_input = (
        f"--- JOB DESCRIPTION ---\n{jd_text}\n\n"
        f"--- CANDIDATE PROFESSIONAL SUMMARY (verified — only source of candidate facts) ---\n{candidate_summary}"
    )
    try:
        result = _call_structured(
            SYSTEM_INSTRUCTION_REFERRAL.format(tone=tone), user_input, ReferralTemplate, temperature=0.6
        )
        return result.message.strip()
    except Exception:
        return "Couldn't generate a referral message right now — please try again in a moment."


class MailTemplate(BaseModel):
    subject: str = Field(description="Short email subject line mentioning the role title.")
    body: str = Field(description="~120-180 word application email body, plain text, no markdown.")

SYSTEM_INSTRUCTION_MAIL = """
Act as a career coach writing a formal job-application email on behalf of a candidate, to a recruiter or hiring manager for the target role.

Rules:
1. Tone: professional and concise, suitable for a first-contact application email.
2. Subject line: short, mentions the role title from the JD.
3. Body length: ~120-180 words.
4. Reference the role title and 2-3 concrete, JD-relevant skills — draw skills ONLY from the candidate's professional summary provided below, never invent skills, employers, or experience not present there.
5. Mention that the resume is attached.
6. Use placeholders in [square brackets] for anything unknowable here: [Hiring Manager's Name], [Your Name], [Your Phone Number], and the company name if the JD doesn't state one.
7. Output plain text only — no markdown formatting.
"""

@st.cache_data(show_spinner=False, ttl=3600, max_entries=50)
def generate_mail_template(jd_text, candidate_summary):
    if not jd_text or not candidate_summary:
        return {"subject": "", "body": ""}
    user_input = (
        f"--- JOB DESCRIPTION ---\n{jd_text}\n\n"
        f"--- CANDIDATE PROFESSIONAL SUMMARY (verified — only source of candidate facts) ---\n{candidate_summary}"
    )
    try:
        result = _call_structured(SYSTEM_INSTRUCTION_MAIL, user_input, MailTemplate, temperature=0.5)
        return {"subject": result.subject.strip(), "body": result.body.strip()}
    except Exception:
        return {"subject": "", "body": "Couldn't generate an application email right now — please try again in a moment."}
