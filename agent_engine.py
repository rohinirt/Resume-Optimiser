import json
import os
import re
import time
from typing import Any

import streamlit as st
from google import genai
from google.genai import types


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured. "
        "Add it to Streamlit secrets or your environment."
    )

client = genai.Client(api_key=api_key)


# ============================================================
# GENERAL HELPERS
# ============================================================

def _get_status_code(error):
    for attr in ("code", "status_code", "http_status", "status"):
        value = getattr(error, attr, None)

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.isdigit():
            return int(value)

    match = re.search(r"\b(429|500|503|404)\b", str(error))

    if match:
        return int(match.group(1))

    return None


def _extract_retry_delay(error, default=2.0):
    match = re.search(
        r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s",
        str(error)
    )

    if match:
        return float(match.group(1))

    return default


import random
import time


def _call_gemini(
    prompt: str,
    schema: dict,
    thinking_level: str = "medium",
    model: str = None,
    max_retries: int = 3
) -> dict:

    models_to_try = []

    if model:
        models_to_try.append(model)

    models_to_try.extend([
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ])

    # Remove duplicates while preserving order
    models_to_try = list(dict.fromkeys(models_to_try))

    last_error = None

    for current_model in models_to_try:

        for attempt in range(max_retries):

            try:

                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        thinking_config=types.ThinkingConfig(
                            thinking_level=thinking_level
                        ),
                    ),
                )

                if not response.text:
                    raise RuntimeError(
                        f"Empty response from {current_model}"
                    )

                return json.loads(response.text)

            except Exception as error:

                last_error = error
                status = _get_status_code(error)

                # Only retry transient failures
                if status in (429, 500, 503):

                    # Exponential backoff + jitter
                    delay = min(
                        30,
                        2 ** attempt
                    ) + random.uniform(0, 1)

                    time.sleep(delay)

                    continue

                # 404 / 400 / authentication etc.
                # should not be hammered repeatedly.
                break

    raise RuntimeError(
        "Gemini API is temporarily unavailable. "
        "Multiple models and retries were attempted. "
        "Please try again in a few minutes."
    ) from last_error


# ============================================================
# SCHEMAS
# ============================================================

JD_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {

        "role_profile": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string"},
                "seniority": {"type": "string"},
                "domain": {"type": "string"},
                "primary_responsibilities": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [
                "job_title",
                "seniority",
                "domain",
                "primary_responsibilities"
            ]
        },

        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {

                    "id": {"type": "string"},

                    "requirement": {
                        "type": "string"
                    },

                    "category": {
                        "type": "string"
                    },

                    "importance": {
                        "type": "string",
                        "enum": [
                            "required",
                            "preferred",
                            "contextual"
                        ]
                    },

                    "type": {
                        "type": "string",
                        "enum": [
                            "skill",
                            "responsibility",
                            "methodology",
                            "domain",
                            "education",
                            "experience",
                            "keyword"
                        ]
                    }
                },

                "required": [
                    "id",
                    "requirement",
                    "category",
                    "importance",
                    "type"
                ]
            }
        },

        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {

                    "id": {
                        "type": "string"
                    },

                    "source": {
                        "type": "string",
                        "enum": [
                            "resume",
                            "experience",
                            "project"
                        ]
                    },

                    "title": {
                        "type": "string"
                    },

                    "evidence": {
                        "type": "string"
                    },

                    "tools": {
                        "type": "array",
                        "items": {"type": "string"}
                    },

                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"}
                    },

                    "domains": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },

                "required": [
                    "id",
                    "source",
                    "title",
                    "evidence",
                    "tools",
                    "metrics",
                    "domains"
                ]
            }
        }
    },

    "required": [
        "role_profile",
        "requirements",
        "evidence"
    ]
}


ALIGNMENT_SCHEMA = {
    "type": "object",

    "properties": {

        "matches": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "requirement_id": {
                        "type": "string"
                    },

                    "match": {
                        "type": "string",
                        "enum": [
                            "full",
                            "partial",
                            "missing"
                        ]
                    },

                    "evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    },

                    "reason": {
                        "type": "string"
                    }
                },

                "required": [
                    "requirement_id",
                    "match",
                    "evidence_ids",
                    "reason"
                ]
            }
        },

        "priority_gaps": {
            "type": "array",
            "items": {"type": "string"}
        },

        "strategy": {
            "type": "array",
            "items": {"type": "string"}
        },

        "project_recommendations": {
            "type": "array",
            "items": {"type": "string"}
        }
    },

    "required": [
        "matches",
        "priority_gaps",
        "strategy",
        "project_recommendations"
    ]
}


RESUME_SCHEMA = {
    "type": "object",

    "properties": {

        "professional_summary": {
            "type": "string"
        },

        "core_competencies_grouped": {
            "type": "object",

            "properties": {
                "Programming & Databases": {
                    "type": "string"
                },

                "Visualization & BI Tools": {
                    "type": "string"
                },

                "Data Engineering & Workflows": {
                    "type": "string"
                },

                "Core Competencies": {
                    "type": "string"
                }
            },

            "required": [
                "Programming & Databases",
                "Visualization & BI Tools",
                "Data Engineering & Workflows",
                "Core Competencies"
            ]
        },

        "professional_experience": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "role_title": {
                        "type": "string"
                    },

                    "bullets": {
                        "type": "array",
                        "items": {"type": "string"}
                    },

                    "evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },

                "required": [
                    "role_title",
                    "bullets",
                    "evidence_ids"
                ]
            }
        },

        "projects": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "project_title": {
                        "type": "string"
                    },

                    "project_link": {
                        "type": "string"
                    },

                    "project_link_label": {
                        "type": "string"
                    },

                    "bullets": {
                        "type": "array",
                        "items": {"type": "string"}
                    },

                    "evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },

                "required": [
                    "project_title",
                    "project_link",
                    "project_link_label",
                    "bullets",
                    "evidence_ids"
                ]
            }
        },

        "education": {
            "type": "array",
            "items": {"type": "string"}
        },

        "certifications": {
            "type": "array",
            "items": {"type": "string"}
        },

        "suggested_filename": {
            "type": "string"
        },

        "summary_of_changes": {
            "type": "array",
            "items": {"type": "string"}
        }
    },

    "required": [
        "professional_summary",
        "core_competencies_grouped",
        "professional_experience",
        "projects",
        "education",
        "certifications",
        "suggested_filename",
        "summary_of_changes"
    ]
}


# ============================================================
# PROMPT 1 — JD + CANDIDATE EVIDENCE EXTRACTION
# ============================================================

def _build_analysis_prompt(
    jd,
    resume,
    experience,
    projects
):

    return f"""
You are the ANALYSIS ENGINE of a resume optimisation system.

Your job is NOT to write a resume.

Your job is to build two structured models:

1. What the target job actually requires.
2. What the candidate can legitimately prove from the supplied documents.

==================================================
CRITICAL TRUTH RULES
==================================================

The Job Description describes requirements.

It does NOT describe candidate experience.

Candidate evidence may only come from the supplied resume,
experience file and projects file.

NEVER infer:

- a technology the candidate has not explicitly demonstrated
- production experience from a personal project
- PostgreSQL from generic SQL
- Power BI from Tableau
- Snowflake from BigQuery
- leadership from participation
- A/B testing from generic analytics
- cloud experience from unrelated tools
- metrics that are not present
- certifications that are not present
- domain experience that is not present

Related experience should be classified later as PARTIAL.

==================================================
JD REQUIREMENT EXTRACTION
==================================================

Extract meaningful requirements.

Prioritise:

- required technical skills
- required responsibilities
- required methodologies
- required domain knowledge
- required experience
- education requirements
- important terminology

Do not treat generic words such as "team", "communication",
"fast-paced", or "motivated" as hard technical keywords unless
they represent a real hiring requirement.

Assign:

required
preferred
contextual

importance.

==================================================
CANDIDATE EVIDENCE EXTRACTION
==================================================

Extract concrete evidence from the candidate documents.

Strong evidence includes:

- tools
- technologies
- responsibilities
- achievements
- metrics
- data volumes
- user counts
- frequency
- business outcomes
- analytical methods
- domains
- project outcomes

Preserve numeric information exactly.

Do not create numbers.

Use stable IDs:

REQ-001, REQ-002...

EVD-001, EVD-002...

==================================================

JOB DESCRIPTION
==================================================

<JD>
{jd}
</JD>

==================================================
MASTER RESUME
==================================================

<MASTER_RESUME>
{resume}
</MASTER_RESUME>

==================================================
ADDITIONAL EXPERIENCE
==================================================

<EXPERIENCE>
{experience}
</EXPERIENCE>

==================================================
PROJECTS
==================================================

<PROJECTS>
{projects}
</PROJECTS>
"""


# ============================================================
# PROMPT 2 — REQUIREMENT / EVIDENCE ALIGNMENT
# ============================================================

def _build_alignment_prompt(
    jd,
    analysis
):

    return f"""
You are the ALIGNMENT ENGINE of a resume optimisation system.

Map each JD requirement to VERIFIED candidate evidence.

Do not write the resume.

==================================================
MATCH DEFINITIONS
==================================================

FULL:

Candidate evidence directly demonstrates the requested
skill, responsibility, methodology or domain.

PARTIAL:

Candidate demonstrates a related capability, but the exact
requirement is not established.

Example:

JD = PostgreSQL
Candidate = SQL

Result = PARTIAL.

JD = Power BI
Candidate = Tableau

Result = PARTIAL.

MISSING:

There is no credible candidate evidence.

==================================================
IMPORTANT
==================================================

Do not upgrade PARTIAL to FULL.

Do not convert a missing requirement into a claimed skill.

Do not recommend inserting a missing skill simply because
it would improve ATS matching.

Strategy should identify existing evidence worth surfacing.

==================================================
PROJECT SELECTION
==================================================

Recommend projects based on:

1. technical overlap
2. responsibility overlap
3. domain relevance
4. business problem similarity
5. strength of available evidence

Do not select a project merely because it contains a keyword.

==================================================
JOB DESCRIPTION
==================================================

<JD>
{jd}
</JD>

==================================================
ANALYSIS
==================================================

<ANALYSIS>
{json.dumps(analysis, indent=2, ensure_ascii=False)}
</ANALYSIS>
"""


# ============================================================
# PROMPT 3 — RESUME WRITER
# ============================================================

def _build_resume_prompt(
    resume,
    experience,
    projects,
    analysis,
    alignment
):

    return f"""
You are the FINAL RESUME WRITER.

Create a targeted, truthful resume using ONLY VERIFIED
candidate evidence.

==================================================
NON-NEGOTIABLE RULES
==================================================

1. Never invent a metric.

2. Never invent a technology.

3. Never invent an employer.

4. Never invent a responsibility.

5. Never invent a certification.

6. Never convert a project into professional experience.

7. Never convert related technology into exact technology.

8. Never insert missing JD keywords without evidence.

9. Never change dates or employers.

10. Never invent URLs.

==================================================
POSITIONING
==================================================

Prioritise:

JD relevance
+
verified evidence
+
business impact
+
clarity
+
recruiter scanability

Do NOT optimise for keyword density alone.

==================================================
SUMMARY
==================================================

Write approximately 45–65 words.

Mention only JD-relevant areas supported by evidence.

Avoid generic claims such as:

"results-driven"
"highly motivated"
"passionate"
"dynamic"

unless directly useful.

==================================================
EXPERIENCE BULLETS
==================================================

Use the XYZ principle when useful:

Action / accomplishment
+
measurable result or real scope
+
method / tool

But DO NOT force identical grammar onto every bullet.

Prefer natural professional language.

Typical target:

18–30 words per bullet.

Preserve important source metrics exactly.

If no metric exists:

use concrete scope, frequency, scale, tools or responsibility.

==================================================
PROJECTS
==================================================

Select up to TWO projects from the evidence.

Choose projects with the strongest alignment.

Each project should have approximately 2–3 bullets.

Only use verified project URLs.

==================================================
SKILLS
==================================================

Only include skills supported by candidate evidence.

Group skills into:

Programming & Databases
Visualization & BI Tools
Data Engineering & Workflows
Core Competencies

==================================================
MARKDOWN
==================================================

Use **bold** only for important:

tools
technologies
metrics
high-impact phrases

No other markup.

==================================================
EVIDENCE PROVENANCE
==================================================

Every professional experience group and project must include
the evidence IDs used to construct it.

==================================================
SOURCE DATA
==================================================

<MASTER_RESUME>
{resume}
</MASTER_RESUME>

<EXPERIENCE>
{experience}
</EXPERIENCE>

<PROJECTS>
{projects}
</PROJECTS>

<ANALYSIS>
{json.dumps(analysis, indent=2, ensure_ascii=False)}
</ANALYSIS>

<ALIGNMENT>
{json.dumps(alignment, indent=2, ensure_ascii=False)}
</ALIGNMENT>
"""


# ============================================================
# VALIDATION
# ============================================================

def _extract_numbers(text):

    return set(
        re.findall(
            r"\b\d+(?:[.,]\d+)?%?\+?\b",
            text or ""
        )
    )


def _collect_source_numbers(
    resume,
    experience,
    projects
):

    return _extract_numbers(
        "\n".join([
            resume or "",
            experience or "",
            projects or ""
        ])
    )


def _all_generated_text(output):

    parts = []

    parts.append(
        output.get("professional_summary", "")
    )

    competencies = output.get(
        "core_competencies_grouped",
        {}
    )

    parts.extend(
        competencies.values()
    )

    for role in output.get(
        "professional_experience",
        []
    ):

        parts.extend(
            role.get("bullets", [])
        )

    for project in output.get(
        "projects",
        []
    ):

        parts.extend(
            project.get("bullets", [])
        )

    parts.extend(
        output.get("education", [])
    )

    parts.extend(
        output.get("certifications", [])
    )

    return "\n".join(parts)


def _validate_metrics(
    output,
    source_numbers
):

    violations = []

    for role in output.get(
        "professional_experience",
        []
    ):

        for bullet in role.get(
            "bullets",
            []
        ):

            generated_numbers = _extract_numbers(
                bullet
            )

            unsupported = (
                generated_numbers
                - source_numbers
            )

            if unsupported:

                violations.append({
                    "type": "unsupported_metric",
                    "text": bullet,
                    "numbers": sorted(
                        unsupported
                    )
                })

    for project in output.get(
        "projects",
        []
    ):

        for bullet in project.get(
            "bullets",
            []
        ):

            generated_numbers = _extract_numbers(
                bullet
            )

            unsupported = (
                generated_numbers
                - source_numbers
            )

            if unsupported:

                violations.append({
                    "type": "unsupported_project_metric",
                    "text": bullet,
                    "numbers": sorted(
                        unsupported
                    )
                })

    return violations


# ============================================================
# DETERMINISTIC SCORING
# ============================================================

IMPORTANCE_WEIGHTS = {
    "required": 1.0,
    "preferred": 0.6,
    "contextual": 0.25
}

MATCH_WEIGHTS = {
    "full": 1.0,
    "partial": 0.5,
    "missing": 0.0
}


def _calculate_keyword_score(
    requirements,
    matches
):

    if not requirements:
        return 0.0

    match_map = {
        item["requirement_id"]: item
        for item in matches
    }

    total_weight = 0.0
    achieved_weight = 0.0

    for requirement in requirements:

        importance = requirement[
            "importance"
        ]

        weight = IMPORTANCE_WEIGHTS.get(
            importance,
            0.25
        )

        total_weight += weight

        match = match_map.get(
            requirement["id"],
            {}
        ).get(
            "match",
            "missing"
        )

        achieved_weight += (
            weight
            * MATCH_WEIGHTS.get(
                match,
                0.0
            )
        )

    if total_weight == 0:
        return 0.0

    return round(
        40 * achieved_weight / total_weight,
        1
    )


def _get_match_lists(
    requirements,
    matches
):

    match_map = {
        item["requirement_id"]: item
        for item in matches
    }

    full = []
    partial = []
    missing = []

    for requirement in requirements:

        status = match_map.get(
            requirement["id"],
            {}
        ).get(
            "match",
            "missing"
        )

        label = requirement[
            "requirement"
        ]

        if status == "full":
            full.append(label)

        elif status == "partial":
            partial.append(label)

        else:
            missing.append(label)

    return full, partial, missing


def _word_count(text):

    return len(
        re.findall(
            r"\b[\w’'-]+\b",
            text or ""
        )
    )


def _length_score(word_count):

    if 600 <= word_count <= 800:
        return 10.0

    if 500 <= word_count < 600:
        return 8.0

    if 800 < word_count <= 900:
        return 8.0

    if 400 <= word_count < 500:
        return 6.0

    if 900 < word_count <= 1000:
        return 6.0

    if 300 <= word_count < 400:
        return 4.0

    if 1000 < word_count <= 1100:
        return 4.0

    return 2.0 if word_count else 0.0


def _formatting_score(
    resume_text
):

    text = resume_text or ""

    checks = [

        bool(
            re.search(
                r"@",
                text
            )
        ),

        bool(
            re.search(
                r"\b(?:EXPERIENCE|PROFESSIONAL EXPERIENCE|WORK EXPERIENCE)\b",
                text,
                re.I
            )
        ),

        bool(
            re.search(
                r"\bEDUCATION\b",
                text,
                re.I
            )
        ),

        bool(
            re.search(
                r"\b(?:SKILLS|TECHNICAL SKILLS)\b",
                text,
                re.I
            )
        ),

        not bool(
            re.search(
                r"[^\\x00-\\x7F]{3,}",
                text
            )
        )
    ]

    return round(
        15 * sum(checks) / len(checks),
        1
    )


def _section_score(
    resume_text
):

    text = resume_text or ""

    checks = [

        bool(
            re.search(
                r"@",
                text
            )
        ),

        bool(
            re.search(
                r"\bEDUCATION\b",
                text,
                re.I
            )
        ),

        bool(
            re.search(
                r"\b(?:CERTIFICATIONS?|CERTIFICATES?)\b",
                text,
                re.I
            )
        )
    ]

    return round(
        10 * sum(checks) / 3,
        1
    )


def _impact_score(
    bullets,
    source_numbers
):

    if not bullets:
        return 0.0

    metric_bullets = 0
    scope_bullets = 0

    for bullet in bullets:

        numbers = _extract_numbers(
            bullet
        )

        if numbers and numbers.issubset(
            source_numbers
        ):

            metric_bullets += 1

        elif re.search(
            r"\b(?:records?|users?|daily|weekly|monthly|global|team|dashboard|pipeline|tickets?|queries?)\b",
            bullet,
            re.I
        ):

            scope_bullets += 1

    ratio = (
        metric_bullets
        + 0.5 * scope_bullets
    ) / len(bullets)

    return round(
        25 * ratio,
        1
    )


def _calculate_resume_score(
    requirements,
    matches,
    resume_text,
    experience_bullets,
    source_text
):

    hard_skills = _calculate_keyword_score(
        requirements,
        matches
    )

    formatting = _formatting_score(
        resume_text
    )

    source_numbers = _collect_source_numbers(
        source_text,
        "",
        ""
    )

    impact = _impact_score(
        experience_bullets,
        source_numbers
    )

    length = _length_score(
        _word_count(resume_text)
    )

    completeness = _section_score(
        resume_text
    )

    total = round(
        hard_skills
        + formatting
        + impact
        + length
        + completeness
    )

    return {
        "score": total,
        "components": {
            "hard_skills": hard_skills,
            "formatting": formatting,
            "impact_metrics": impact,
            "length_brevity": length,
            "section_completeness": completeness
        }
    }


# ============================================================
# PUBLIC PIPELINE
# ============================================================

def analyze_and_optimize_resume(
    master_resume_text,
    projects_text,
    experience_text,
    jd_text
):

    # --------------------------------------------------------
    # STAGE 1
    # JD + candidate evidence extraction
    # --------------------------------------------------------

    analysis = _call_gemini(
        _build_analysis_prompt(
            jd_text,
            master_resume_text,
            experience_text,
            projects_text
        ),
        JD_ANALYSIS_SCHEMA,
        thinking_level="medium",
        max_retries=1
    )

    # --------------------------------------------------------
    # STAGE 2
    # Evidence ↔ JD alignment
    # --------------------------------------------------------

    alignment = _call_gemini(
        _build_alignment_prompt(
            jd_text,
            analysis
        ),
        ALIGNMENT_SCHEMA,
        thinking_level="medium",
        max_retries=1
    )

    # --------------------------------------------------------
    # STAGE 3
    # Resume generation
    # --------------------------------------------------------

    generated = _call_gemini(
        _build_resume_prompt(
            master_resume_text,
            experience_text,
            projects_text,
            analysis,
            alignment
        ),
        RESUME_SCHEMA,
        thinking_level="high",
        max_retries=1
    )

    # --------------------------------------------------------
    # STAGE 4
    # Evidence validation
    # --------------------------------------------------------

    source_numbers = _collect_source_numbers(
        master_resume_text,
        experience_text,
        projects_text
    )

    validation_errors = _validate_metrics(
        generated,
        source_numbers
    )

    # If unsupported metrics were generated,
    # ask Gemini to repair them.
    if validation_errors:

        repair_prompt = f"""
You are a resume validation and repair engine.

The generated resume contains unsupported numerical claims.

Remove or rewrite ONLY unsupported numerical claims.

Do not introduce new information.

Do not change supported claims unnecessarily.

SOURCE EVIDENCE:

{master_resume_text}

{experience_text}

{projects_text}

CURRENT OUTPUT:

{json.dumps(
    generated,
    indent=2,
    ensure_ascii=False
)}

VALIDATION ERRORS:

{json.dumps(
    validation_errors,
    indent=2
)}

Return the corrected resume using exactly the same schema.
"""

        generated = _call_gemini(
            repair_prompt,
            RESUME_SCHEMA,
            thinking_level="medium",
            max_retries=0
        )

    # --------------------------------------------------------
    # STAGE 5
    # Deterministic scoring
    # --------------------------------------------------------

    requirements = analysis[
        "requirements"
    ]

    matches = alignment[
        "matches"
    ]

    full_matches, partial_matches, missing_matches = (
        _get_match_lists(
            requirements,
            matches
        )
    )

    original_bullets = re.findall(
        r"(?m)^\s*(?:[•*-])\s+(.+)$",
        master_resume_text or ""
    )

    generated_bullets = [
        bullet
        for role in generated.get(
            "professional_experience",
            []
        )
        for bullet in role.get(
            "bullets",
            []
        )
    ]

    pre_score = _calculate_resume_score(
        requirements=requirements,
        matches=matches,
        resume_text=master_resume_text,
        experience_bullets=original_bullets,
        source_text="\n".join([
            master_resume_text,
            experience_text,
            projects_text
        ])
    )

    generated_text = _all_generated_text(
        generated
    )

    post_score = _calculate_resume_score(
        requirements=requirements,
        matches=matches,
        resume_text=generated_text,
        experience_bullets=generated_bullets,
        source_text="\n".join([
            master_resume_text,
            experience_text,
            projects_text
        ])
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    role_profile = analysis[
        "role_profile"
    ]

    responsibilities = role_profile.get(
        "primary_responsibilities",
        []
    )

    responsibility_text = ", ".join(
        responsibilities[:3]
    )

    return {

        "pre_optimization": {

            "ats_score": pre_score["score"],

            "matching_keywords": full_matches,

            "partial_matches": partial_matches,

            "missing_keywords": missing_matches
        },

        "post_optimization": {

            "ats_score": post_score["score"],

            "matching_keywords": full_matches,

            "partial_matches": partial_matches,

            "missing_keywords": missing_matches
        },

        "audit_categories": {

            "hard_skills": {

                "score": post_score[
                    "components"
                ]["hard_skills"],

                "feedback": (
                    f"Weighted requirement coverage: "
                    f"{len(full_matches)} full matches, "
                    f"{len(partial_matches)} partial matches, "
                    f"{len(missing_matches)} missing."
                ),

                "actionable_fixes": [
                    f"Only add missing requirements when genuine evidence exists: "
                    f"{', '.join(missing_matches[:6]) or 'none identified'}."
                ]
            },

            "formatting": {

                "score": post_score[
                    "components"
                ]["formatting"],

                "feedback": (
                    "Basic ATS-parsability checks based on "
                    "standard headings and extracted text."
                ),

                "actionable_fixes": [
                    "Keep standard section headings and consistent formatting."
                ]
            },

            "impact_metrics": {

                "score": post_score[
                    "components"
                ]["impact_metrics"],

                "feedback": (
                    "Scores sourced numeric metrics fully and "
                    "real scope descriptions partially."
                ),

                "actionable_fixes": [
                    "Add real metrics to the evidence repository "
                    "when they exist."
                ]
            },

            "length_brevity": {

                "score": post_score[
                    "components"
                ]["length_brevity"],

                "feedback": (
                    f"Generated content contains "
                    f"{_word_count(generated_text)} words."
                ),

                "actionable_fixes": [
                    "Trim low-priority content if the final document becomes too long."
                ]
            },

            "section_completeness": {

                "score": post_score[
                    "components"
                ]["section_completeness"],

                "feedback": (
                    "Checks presence of contact information, "
                    "education and certifications."
                ),

                "actionable_fixes": [
                    "Keep education and certifications current."
                ]
            }
        },

        "fitness_and_strategy": {

            "role_fitness_summary": (
                f"{role_profile.get('job_title', 'Target role')} "
                f"({role_profile.get('seniority', 'unspecified seniority')}) "
                f"emphasises "
                f"{responsibility_text or 'the responsibilities specified in the JD'}."
            ),

            "gaps_and_missing_elements": (
                ", ".join(
                    alignment.get(
                        "priority_gaps",
                        []
                    )
                )
                or "No high-priority evidence gaps identified."
            ),

            "alignment_strategy": alignment.get(
                "strategy",
                []
            )
        },

        "summary_of_changes": generated.get(
            "summary_of_changes",
            []
        ),

        "section_2_tailored_content": {

            "contact_info": {
                "name": "",
                "details": ""
            },

            "professional_summary": generated.get(
                "professional_summary",
                ""
            ),

            "core_competencies_grouped": generated.get(
                "core_competencies_grouped",
                {}
            ),

            "professional_experience": generated.get(
                "professional_experience",
                []
            ),

            "projects": generated.get(
                "projects",
                []
            ),

            "education": generated.get(
                "education",
                []
            ),

            "certifications": generated.get(
                "certifications",
                []
            )
        },

        "suggested_filename": generated.get(
            "suggested_filename",
            "Tailored_Resume"
        ),

        "salary_benchmark": (
            "Salary benchmarking is intentionally separated "
            "from resume optimisation."
        ),

        "pipeline_meta": {

            "model": PRIMARY_MODEL,

            "stages": [
                "jd_analysis",
                "candidate_evidence_extraction",
                "requirement_alignment",
                "resume_generation",
                "evidence_validation",
                "deterministic_scoring"
            ],

            "validation_errors_found": len(
                validation_errors
            )
        }
    }


# ============================================================
# LEGACY SALARY FUNCTION
# ============================================================
# Kept here so the existing app does not break immediately.
# We will remove this from the workflow in the next iteration.

def fetch_real_web_salary(company_name, role="Data Analyst"):

    return {
        "company": company_name,
        "role": role,
        "status": "disabled",
        "message": (
            "Salary benchmarking is currently separated "
            "from resume optimisation."
        )
    }
