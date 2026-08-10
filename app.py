import streamlit as st
import streamlit.components.v1 as components

from utils import (
    extract_text_from_file,
    generate_standard_resume_sheet_html,
    generate_paper_sheet_tailored_html,
    generate_new_formatted_docx
)

from agent_engine import (
    analyze_and_optimize_resume,
    fetch_real_web_salary
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ResumeTarget | ATS Optimization",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state["page"] = "landing"

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Analysis"

if "results" not in st.session_state:
    st.session_state["results"] = {}

if "resume_bytes" not in st.session_state:
    st.session_state["resume_bytes"] = b""

if "file_type" not in st.session_state:
    st.session_state["file_type"] = "pdf"

if "file_name" not in st.session_state:
    st.session_state["file_name"] = ""


def go_to_landing():
    st.session_state["page"] = "landing"


# ============================================================
# GLOBAL STYLING
# ============================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: "Inter", sans-serif !important;
    }

    .stApp {
        background: #f8fafc !important;
        color: #0f172a !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Hide Streamlit sidebar completely */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* --------------------------------------------------------
       GENERIC CARDS
       -------------------------------------------------------- */

    .panel-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.025);
        margin-bottom: 18px;
    }

    .panel-title {
        font-weight: 800;
        font-size: 1rem;
        color: #0f172a;
        margin-bottom: 14px;
    }

    /* --------------------------------------------------------
       LANDING PAGE
       -------------------------------------------------------- */

    .hero-container {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        padding: 48px;
        border-radius: 20px;
        color: #0f172a;
        margin-bottom: 32px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.03);
        text-align: center;
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 12px;
        color: #0f172a;
    }

    .hero-subtitle {
        color: #64748b;
        font-size: 1.1rem;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.5;
    }

    .upload-section-wrapper {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 32px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 30px;
    }

    .feature-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }

    .feature-title {
        color: #2563eb;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 8px;
    }

    /* --------------------------------------------------------
       TAGS
       -------------------------------------------------------- */

    .tag-green {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
        margin: 3px;
    }

    .tag-red {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
        margin: 3px;
    }

    /* --------------------------------------------------------
       HEADER
       -------------------------------------------------------- */

    .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding-top: 4px;
    }

    .brand-icon {
        background: #2563eb;
        color: #ffffff;
        width: 34px;
        height: 34px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.1rem;
    }

    .brand-name {
        font-size: 1.3rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
    }

    /* Native Streamlit segmented control */
    div[data-testid="stSegmentedControl"] {
        justify-content: center;
    }

    div[data-testid="stSegmentedControl"] button {
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        min-height: 40px !important;
        padding: 0 22px !important;
    }

    /* Download button */
    div[data-testid="stDownloadButton"] button {
        border: 1px solid #2563eb !important;
        color: #2563eb !important;
        background: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        min-height: 40px !important;
    }

    /* Change file button */
    div[data-testid="stButton"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* --------------------------------------------------------
       SCORE
       -------------------------------------------------------- */

    .score-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 18px;
        min-width: 170px;
    }

    .score-label {
        font-size: 0.68rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .score-status {
        font-size: 0.74rem;
        color: #16a34a;
        font-weight: 700;
        margin-top: 2px;
    }

    .score-number {
        font-size: 1.7rem;
        font-weight: 800;
        color: #16a34a;
        white-space: nowrap;
    }

    .score-number span {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
    }

    /* --------------------------------------------------------
       BREAKDOWN
       -------------------------------------------------------- */

    .metric-row {
        margin-bottom: 18px;
    }

    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 7px;
        font-size: 0.84rem;
    }

    .metric-label {
        font-weight: 600;
        color: #334155;
    }

    .metric-value {
        font-weight: 700;
        color: #475569;
    }

    .metric-track {
        width: 100%;
        height: 7px;
        background: #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
    }

    .metric-fill {
        height: 100%;
        border-radius: 10px;
    }

    /* --------------------------------------------------------
       SUMMARY
       -------------------------------------------------------- */

    .summary-score-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 16px;
    }

    .summary-score {
        padding: 14px;
    }

    .summary-score + .summary-score {
        border-left: 1px solid #e2e8f0;
    }

    .summary-score-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
    }

    .summary-score-value {
        font-size: 1.35rem;
        font-weight: 800;
        margin-top: 3px;
    }

    .summary-score-good {
        color: #15803d;
    }

    .summary-score-gap {
        color: #dc2626;
    }

    .summary-score-status {
        font-size: 0.72rem;
        font-weight: 600;
        margin-top: 2px;
    }

    .summary-text {
        color: #475569;
        font-size: 0.84rem;
        line-height: 1.6;
    }

    /* --------------------------------------------------------
       STRATEGY
       -------------------------------------------------------- */

    .strategy-item {
        display: flex;
        gap: 9px;
        margin-bottom: 10px;
        color: #475569;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    .strategy-check {
        color: #16a34a;
        font-weight: 800;
        flex-shrink: 0;
    }

    /* --------------------------------------------------------
       ENHANCEMENT ITEMS
       -------------------------------------------------------- */

    .enhancement-item {
        padding: 12px 0;
        border-bottom: 1px solid #eef2f7;
    }

    .enhancement-item:last-child {
        border-bottom: none;
    }

    .enhancement-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }

    .enhancement-text {
        font-size: 0.78rem;
        color: #64748b;
        line-height: 1.5;
    }

    .privacy-footer {
        text-align: center;
        color: #64748b;
        font-size: 0.75rem;
        padding: 4px 0 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PAGE 1: LANDING PAGE
# ============================================================

if st.session_state["page"] == "landing":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">ResumeTarget</div>
            <div class="hero-subtitle">
                High-Precision ATS Optimization & Executive Resume
                Tailoring Engine. Built for rigorous algorithmic matching
                and recruiter impact.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Step 1: Provide Source Files & Target Job Description")

    st.markdown(
        '<div class="upload-section-wrapper">',
        unsafe_allow_html=True
    )

    uc1, uc2, uc3, uc4 = st.columns(4)

    with uc1:
        uploaded_resume = st.file_uploader(
            "Master Resume (.pdf / .docx)",
            type=["pdf", "docx"],
            key="upload_resume"
        )

    with uc2:
        uploaded_experience = st.file_uploader(
            "Experience File (.pdf / .docx)",
            type=["pdf", "docx"],
            key="upload_exp"
        )

    with uc3:
        uploaded_projects = st.file_uploader(
            "Projects Repository (.pdf / .docx)",
            type=["pdf", "docx"],
            key="upload_proj"
        )

    with uc4:
        jd_input = st.text_area(
            "Target Job Description (JD)",
            height=140,
            placeholder="Paste job requirements..."
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    analyze_btn = st.button(
        "Initialize ATS Audit & Tailoring Workspace",
        type="primary",
        use_container_width=True
    )

    if analyze_btn:

        if not uploaded_resume or not jd_input:

            st.warning(
                "Please upload a Master Resume and paste a Job Description to proceed."
            )

        else:

            with st.spinner(
                "Executing semantic keyword mapping, gap analysis, and layout generation..."
            ):

                file_bytes = uploaded_resume.read()
                uploaded_resume.seek(0)

                st.session_state["resume_bytes"] = file_bytes
                st.session_state["file_type"] = (
                    uploaded_resume.name.split(".")[-1].lower()
                )
                st.session_state["file_name"] = uploaded_resume.name

                resume_text = extract_text_from_file(uploaded_resume)

                experience_text = (
                    extract_text_from_file(uploaded_experience)
                    if uploaded_experience
                    else ""
                )

                projects_text = (
                    extract_text_from_file(uploaded_projects)
                    if uploaded_projects
                    else ""
                )

                results = analyze_and_optimize_resume(
                    resume_text,
                    projects_text,
                    experience_text,
                    jd_input
                )

                filename_parts = results.get(
                    "suggested_filename",
                    ""
                ).split("_")

                company_name = (
                    filename_parts[-1]
                    if len(filename_parts) > 1
                    else ""
                )

                real_salary = fetch_real_web_salary(
                    company_name,
                    "Data Analyst"
                )

                results["salary_benchmark"] = real_salary

                st.session_state["results"] = results
                st.session_state["page"] = "results"
                st.session_state["active_tab"] = "Analysis"

                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Workflow Architecture")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">Semantic Gap Analysis</div>
                <p style="font-size:0.85rem;color:#64748b;">
                    Evaluates technical coverage against JD requirements.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">Google XYZ Rewrites</div>
                <p style="font-size:0.85rem;color:#64748b;">
                    Restructures bullet points for quantifiable impact.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">Dual Sheet Previews</div>
                <p style="font-size:0.85rem;color:#64748b;">
                    Compare original vs optimized layout side-by-side.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f4:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-title">Executive Word Export</div>
                <p style="font-size:0.85rem;color:#64748b;">
                    Generates 1-page A4 formatted .docx documents.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# PAGE 2: RESULTS WORKSPACE
# ============================================================

elif st.session_state["page"] == "results":

    res = st.session_state.get("results", {})
    post = res.get("post_optimization", {})
    audit = res.get("audit_categories", {})
    fitness = res.get("fitness_and_strategy", {})

    active_tab = st.session_state.get(
        "active_tab",
        "Analysis"
    )


    # ========================================================
    # TOP NAVIGATION
    # ========================================================

    col_logo, col_spacer, col_toggle, col_download = st.columns(
        [1.2, 1.0, 1.5, 0.8]
    )

    with col_logo:

        st.markdown(
            """
            <div class="brand">
                <div class="brand-icon">R</div>
                <div class="brand-name">ResumeTarget</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_toggle:

        selected_view = st.segmented_control(
            "Resume View",
            ["Analysis", "Optimized Resume"],
            default=active_tab,
            key="resume_view_toggle",
            label_visibility="collapsed"
        )

        if selected_view != st.session_state["active_tab"]:

            st.session_state["active_tab"] = selected_view
            st.rerun()

    with col_download:

        updated_docx = generate_new_formatted_docx(res)

        filename = (
            res.get(
                "suggested_filename",
                "Tailored_Resume"
            )
            + ".docx"
        )

        st.download_button(
            label="Download",
            data=updated_docx,
            file_name=filename,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            key="download_report",
            use_container_width=True
        )

    st.markdown(
        "<hr style='margin:12px 0 20px 0;border-color:#e2e8f0;'>",
        unsafe_allow_html=True
    )


    # ========================================================
    # MAIN 50 / 50 LAYOUT
    # ========================================================

    left_col, right_col = st.columns(
        [1, 1],
        gap="large"
    )


    # ========================================================
    # LEFT: ORIGINAL RESUME
    # ========================================================

    with left_col:

        st.markdown(
            '<div class="panel-card">',
            unsafe_allow_html=True
        )

        hdr_l1, hdr_l2 = st.columns([2.2, 1])

        with hdr_l1:

            st.markdown(
                f"""
                <div style="
                    font-weight:800;
                    font-size:1.15rem;
                    color:#0f172a;
                ">
                    Uploaded Resume
                </div>

                <div style="
                    font-size:0.85rem;
                    color:#64748b;
                    margin-top:2px;
                ">
                    {st.session_state.get("file_name", "Resume.pdf")}
                </div>
                """,
                unsafe_allow_html=True
            )

        with hdr_l2:

            st.button(
                "Change File",
                on_click=go_to_landing,
                key="change_file_btn",
                use_container_width=True
            )

        st.markdown(
            "<div style='margin-top:16px;'></div>",
            unsafe_allow_html=True
        )

        file_type = st.session_state.get("file_type", "pdf")
        resume_bytes = st.session_state.get("resume_bytes", b"")

        if file_type == "docx":

            orig_html = generate_standard_resume_sheet_html(
                "Original Resume",
                resume_bytes,
                is_docx_file=True
            )

        else:

            uploaded_resume_for_pdf = st.session_state.get(
                "upload_resume"
            )

            orig_text = (
                extract_text_from_file(uploaded_resume_for_pdf)
                if uploaded_resume_for_pdf
                else ""
            )

            orig_html = generate_standard_resume_sheet_html(
                "Original Resume",
                orig_text,
                is_docx_file=False
            )

        components.html(
            orig_html,
            height=850,
            scrolling=True
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # ========================================================
    # RIGHT: ANALYSIS OR OPTIMIZED RESUME
    # ========================================================

    with right_col:

        # ====================================================
        # ANALYSIS VIEW
        # ====================================================

        if active_tab == "Analysis":

            overall_score = post.get("ats_score", 86)


            # ------------------------------------------------
            # HEADER + ATS SCORE
            # ------------------------------------------------

            st.markdown(
                f"""
                <div class="panel-card"
                     style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        gap:20px;
                     ">

                    <div>

                        <div style="
                            font-weight:800;
                            font-size:1.15rem;
                            color:#0f172a;
                        ">
                            Analysis & Optimization
                        </div>

                        <div style="
                            font-size:0.85rem;
                            color:#64748b;
                            margin-top:4px;
                        ">
                            Review your resume analysis against
                            job description requirements.
                        </div>

                    </div>

                    <div class="score-card">

                        <div>

                            <div class="score-label">
                                Overall ATS Score
                            </div>

                            <div class="score-status">
                                Great Match!
                            </div>

                        </div>

                        <div class="score-number">
                            {overall_score}
                            <span>/100</span>
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


            # ------------------------------------------------
            # ROW 1:
            # COLUMN 1 = MATCH BREAKDOWN
            # COLUMN 2 = RESUME ANALYSIS SUMMARY
            # ------------------------------------------------

            row1_col1, row1_col2 = st.columns(
                [1, 1],
                gap="medium"
            )


            with row1_col1:

                breakdown_metrics = [
                    (
                        "Skills",
                        audit.get(
                            "hard_skills",
                            {}
                        ).get(
                            "score",
                            90
                        )
                    ),
                    (
                        "Keywords",
                        audit.get(
                            "keywords",
                            {}
                        ).get(
                            "score",
                            85
                        )
                    ),
                    (
                        "Experience",
                        audit.get(
                            "experience",
                            {}
                        ).get(
                            "score",
                            88
                        )
                    ),
                    (
                        "Impact & Metrics",
                        audit.get(
                            "impact_metrics",
                            {}
                        ).get(
                            "score",
                            75
                        )
                    ),
                    (
                        "Formatting",
                        audit.get(
                            "formatting",
                            {}
                        ).get(
                            "score",
                            80
                        )
                    )
                ]

                breakdown_html = ""

                for label, value in breakdown_metrics:

                    try:
                        value = int(value)
                    except:
                        value = 0

                    value = max(0, min(100, value))

                    bar_color = (
                        "#f59e0b"
                        if value < 80
                        else "#16a34a"
                    )

                    breakdown_html += f"""
                    <div class="metric-row">

                        <div class="metric-header">

                            <span class="metric-label">
                                {label}
                            </span>

                            <span class="metric-value">
                                {value}%
                            </span>

                        </div>

                        <div class="metric-track">

                            <div
                                class="metric-fill"
                                style="
                                    width:{value}%;
                                    background:{bar_color};
                                "
                            ></div>

                        </div>

                    </div>
                    """

                st.markdown(
                    f"""
                    <div class="panel-card"
                         style="min-height:350px;">

                        <div class="panel-title">
                            Match Breakdown
                        </div>

                        {breakdown_html}

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            with row1_col2:

                role_fitness = fitness.get(
                    "role_fitness_summary",
                    "Strong analytical foundation matching the core technical requirements."
                )

                gaps = fitness.get(
                    "gaps_and_missing_elements",
                    "Minor gaps remain in some advanced requirements."
                )

                try:
                    fitness_score = int(overall_score)
                except:
                    fitness_score = 86

                gap_score = max(
                    0,
                    100 - fitness_score
                )

                st.markdown(
                    f"""
                    <div class="panel-card"
                         style="min-height:350px;">

                        <div class="panel-title">
                            Resume Analysis Summary
                        </div>

                        <div class="summary-score-grid">

                            <div class="summary-score">

                                <div class="summary-score-label">
                                    Fitness Score
                                </div>

                                <div class="
                                    summary-score-value
                                    summary-score-good
                                ">
                                    {fitness_score}/100
                                </div>

                                <div class="
                                    summary-score-status
                                    summary-score-good
                                ">
                                    Strong Match
                                </div>

                            </div>

                            <div class="summary-score">

                                <div class="summary-score-label">
                                    Gap Score
                                </div>

                                <div class="
                                    summary-score-value
                                    summary-score-gap
                                ">
                                    {gap_score}/100
                                </div>

                                <div class="
                                    summary-score-status
                                    summary-score-gap
                                ">
                                    Improvement Needed
                                </div>

                            </div>

                        </div>

                        <div class="summary-text">

                            <strong>Role Fitness:</strong><br>
                            {role_fitness}

                            <br><br>

                            <strong>Key Gaps:</strong><br>
                            {gaps}

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            # ------------------------------------------------
            # ROW 2:
            # COLUMN 1 = MATCHING + MISSING
            # COLUMN 2 = ENHANCEMENT STRATEGY
            # ------------------------------------------------

            row2_col1, row2_col2 = st.columns(
                [1, 1],
                gap="medium"
            )


            with row2_col1:

                matching_kws = post.get(
                    "matching_keywords",
                    [
                        "SQL",
                        "Python",
                        "Tableau",
                        "Excel",
                        "Pandas",
                        "Power BI",
                        "Data Analysis",
                        "Statistics",
                        "Data Visualization",
                        "Looker Studio",
                        "BigQuery",
                        "ETL Pipelines"
                    ]
                )

                missing_kws = post.get(
                    "missing_keywords",
                    [
                        "Machine Learning",
                        "Data Modeling",
                        "A/B Testing"
                    ]
                )

                matching_tags = "".join(
                    [
                        f'<span class="tag-green">✓ {k}</span>'
                        for k in matching_kws
                    ]
                )

                missing_tags = "".join(
                    [
                        f'<span class="tag-red">✕ {k}</span>'
                        for k in missing_kws
                    ]
                )

                st.markdown(
                    f"""
                    <div class="panel-card"
                         style="min-height:300px;">

                        <div class="panel-title">
                            Matching & Missing Keywords
                        </div>

                        <div style="
                            background:#f0fdf4;
                            border:1px solid #bbf7d0;
                            border-radius:12px;
                            padding:12px;
                            margin-bottom:12px;
                        ">

                            <div style="
                                font-size:0.78rem;
                                font-weight:700;
                                color:#15803d;
                                margin-bottom:6px;
                            ">
                                Matching ({len(matching_kws)})
                            </div>

                            <div>
                                {matching_tags}
                            </div>

                        </div>

                        <div style="
                            background:#fef2f2;
                            border:1px solid #fecaca;
                            border-radius:12px;
                            padding:12px;
                        ">

                            <div style="
                                font-size:0.78rem;
                                font-weight:700;
                                color:#b91c1c;
                                margin-bottom:6px;
                            ">
                                Missing ({len(missing_kws)})
                            </div>

                            <div>
                                {missing_tags}
                            </div>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            with row2_col2:

                enhancement_summary = fitness.get(
                    "enhancement_summary",
                    "Strengthen alignment between your existing experience and the target job description."
                )

                keywords_added = post.get(
                    "keywords_added",
                    []
                )

                skills_added = post.get(
                    "skills_added",
                    []
                )

                rewritten_bullets = post.get(
                    "rewritten_bullet_points",
                    []
                )

                if not keywords_added:
                    keywords_added = [
                        "Relevant JD keywords",
                        "Role-specific terminology"
                    ]

                if not skills_added:
                    skills_added = [
                        "Relevant technical skills"
                    ]

                if not rewritten_bullets:
                    rewritten_bullets = [
                        "Existing bullets rewritten to emphasize measurable impact and outcomes."
                    ]

                keyword_preview = ", ".join(
                    str(x)
                    for x in keywords_added[:6]
                )

                skills_preview = ", ".join(
                    str(x)
                    for x in skills_added[:6]
                )

                bullet_count = len(
                    rewritten_bullets
                )

                st.markdown(
                    f"""
                    <div class="panel-card"
                         style="min-height:300px;">

                        <div class="panel-title">
                            Resume Enhancement Strategy
                        </div>

                        <div class="enhancement-item">

                            <div class="enhancement-title">
                                Quick Summary
                            </div>

                            <div class="enhancement-text">
                                {enhancement_summary}
                            </div>

                        </div>

                        <div class="enhancement-item">

                            <div class="enhancement-title">
                                Keywords Added
                            </div>

                            <div class="enhancement-text">
                                {keyword_preview}
                            </div>

                        </div>

                        <div class="enhancement-item">

                            <div class="enhancement-title">
                                Skills Added
                            </div>

                            <div class="enhancement-text">
                                {skills_preview}
                            </div>

                        </div>

                        <div class="enhancement-item">

                            <div class="enhancement-title">
                                Rewritten Bullet Points
                            </div>

                            <div class="enhancement-text">
                                {bullet_count} bullet point(s)
                                rewritten to improve clarity,
                                relevance, and measurable impact.
                            </div>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            # ------------------------------------------------
            # JOB COMPATIBILITY / ALIGNMENT STRATEGY
            # FULL WIDTH CARD
            # ------------------------------------------------

            strat_points = fitness.get(
                "alignment_strategy",
                [
                    "Highlight automated ETL data processing pipelines and record scale.",
                    "Position technical competencies upfront for immediate ATS keyword weighting.",
                    "Ensure bullet points strictly adhere to the Google XYZ impact formula."
                ]
            )

            strategy_list_html = ""

            for strat in strat_points:

                strategy_list_html += f"""
                <div class="strategy-item">

                    <div class="strategy-check">
                        ✓
                    </div>

                    <div>
                        {strat}
                    </div>

                </div>
                """

            st.markdown(
                f"""
                <div class="panel-card">

                    <div class="panel-title">
                        Job Compatibility & Alignment Strategy
                    </div>

                    <div style="
                        font-size:0.84rem;
                        color:#334155;
                        line-height:1.65;
                        margin-bottom:14px;
                    ">

                        <strong>Role Fitness Summary:</strong>
                        {role_fitness}

                    </div>

                    <div style="
                        font-size:0.84rem;
                        color:#334155;
                        line-height:1.65;
                        margin-bottom:16px;
                    ">

                        <strong>Gaps & Missing Elements:</strong>
                        {gaps}

                    </div>

                    <div style="
                        font-weight:700;
                        font-size:0.88rem;
                        color:#0f172a;
                        margin-bottom:10px;
                    ">
                        Strategic Alignment Roadmap
                    </div>

                    <div>
                        {strategy_list_html}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


        # ====================================================
        # OPTIMIZED RESUME VIEW
        # ====================================================

        else:

            st.markdown(
                """
                <div class="panel-card">

                    <div style="
                        font-weight:800;
                        font-size:1.15rem;
                        color:#0f172a;
                    ">
                        Optimized Resume Preview
                    </div>

                    <div style="
                        font-size:0.85rem;
                        color:#64748b;
                        margin-top:4px;
                    ">
                        Fully tailored, executive-formatted
                        A4 document ready for export.
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            paper_html = generate_paper_sheet_tailored_html(res)

            components.html(
                paper_html,
                height=880,
                scrolling=True
            )


    # ========================================================
    # PRIVACY FOOTER
    # ========================================================

    st.markdown(
        """
        <div class="privacy-footer">
            🔒 Your data is secure and confidential.
            We do not store or share your files.
        </div>
        """,
        unsafe_allow_html=True
  
