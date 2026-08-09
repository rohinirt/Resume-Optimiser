import streamlit as st
from utils import (
    extract_text_from_file, 
    get_pdf_preview_html, 
    get_docx_preview_text, 
    build_updated_docx_inplace
)
from agent_engine import analyze_and_optimize_resume, fetch_real_web_salary

st.set_page_config(
    page_title="ResumeAI Pro | ATS Optimizer", 
    page_icon="⚡", 
    layout="wide"
)

# MODERN LIGHT THEME SAAS STYLING
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Global Light Theme Background */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    /* Header Container */
    .hero-nav {
        background: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .hero-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    /* Style Streamlit File Uploaders & Text Areas */
    [data-testid="stFileUploader"] {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 10px;
        transition: border-color 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #6366f1;
    }

    textarea {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
    }

    /* Action Button */
    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
    }

    /* Keyword Tags */
    .tag-green {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 3px;
    }
    
    .tag-red {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 3px;
    }

    /* Streamlit Expander styling */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# HERO TOP NAVBAR
st.markdown("""
<div class="hero-nav">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 2rem;">⚡</span>
        <div>
            <h1 class="hero-title">ResumeAI Tailor Pro</h1>
            <p class="hero-subtitle">Optimize Master Resumes against Job Descriptions with in-place document formatting.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# SECTION 1: UPLOADS & INPUTS
st.markdown("##### 📥 Step 1: Upload Documents & Job Details")

col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])

with col1:
    uploaded_resume = st.file_uploader("Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")

with col2:
    uploaded_experience = st.file_uploader("Work Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")

with col3:
    uploaded_projects = st.file_uploader("Projects Repository (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")

with col4:
    jd_input = st.text_area("Job Description (JD)", height=130, placeholder="Paste JD responsibilities and key technical requirements...")

st.markdown("<br>", unsafe_allow_html=True)
analyze_btn = st.button("✨ Optimize & Align Resume", type="primary", use_container_width=True)

if analyze_btn and uploaded_resume and jd_input:
    with st.spinner("Analyzing keyword density, fetching live web salary references, and re-writing bullet points..."):
        file_bytes = uploaded_resume.read()
        uploaded_resume.seek(0)
        st.session_state['resume_bytes'] = file_bytes
        st.session_state['file_type'] = uploaded_resume.name.split(".")[-1].lower()
        
        # Parse inputs
        resume_text = extract_text_from_file(uploaded_resume)
        experience_text = extract_text_from_file(uploaded_experience) if uploaded_experience else ""
        projects_text = extract_text_from_file(uploaded_projects) if uploaded_projects else ""
        
        # Call AI Engine
        results = analyze_and_optimize_resume(resume_text, projects_text, experience_text, jd_input)
        
        # Fetch Web Salary via Gemini Google Search
        filename_parts = results.get("suggested_filename", "").split("_")
        company_name = filename_parts[-1] if len(filename_parts) > 1 else ""
        real_salary = fetch_real_web_salary(company_name, "Data Analyst")
        results["salary_benchmark"] = real_salary

        st.session_state['results'] = results

st.markdown("---")

# SECTION 2: RESULTS DASHBOARD & LIVE PREVIEW
if 'results' in st.session_state:
    res = st.session_state['results']
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    fitness = res.get("fitness_and_strategy", {})
    sec2 = res.get("section_2_tailored_content", {})

    st.markdown("##### 📊 Step 2: Review Optimizations & Export")
    
    col_left, col_right = st.columns([1, 1.1])

    # LEFT COLUMN: LIVE ORIGINAL RESUME PREVIEW
    with col_left:
        st.subheader("👁️ Document Preview")
        if st.session_state.get('file_type') == 'pdf':
            st.markdown(get_pdf_preview_html(st.session_state['resume_bytes']), unsafe_allow_html=True)
        else:
            text_preview = get_docx_preview_text(uploaded_resume) if uploaded_resume else ""
            st.text_area("Original File View", text_preview, height=720, disabled=True)

    # RIGHT COLUMN: ANALYTICS & SECTION CONTROLS
    with col_right:
        st.subheader("⚡ Optimization Score & Keywords")

        # SCORE METRIC CARDS
        m1, m2 = st.columns(2)
        m1.metric("Pre-ATS Match Score", f"{pre.get('ats_score', 0)}%")
        m2.metric("Post-ATS Match Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # KEYWORD BADGES
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.markdown("###### 🔴 Pre-Optimization Keywords")
            m_tags = "".join([f'<span class="tag-green">{k}</span>' for k in pre.get('matching_keywords', [])])
            st.markdown(f"**Matching:**<br>{m_tags}", unsafe_allow_html=True)
            
            missing_tags = "".join([f'<span class="tag-red">{k}</span>' for k in pre.get('missing_keywords', [])])
            st.markdown(f"**Missing:**<br>{missing_tags}", unsafe_allow_html=True)

        with k_col2:
            st.markdown("###### 🟢 Post-Optimization Keywords")
            m_tags_post = "".join([f'<span class="tag-green">{k}</span>' for k in post.get('matching_keywords', [])])
            st.markdown(f"**Matching:**<br>{m_tags_post}", unsafe_allow_html=True)
            
            missing_tags_post = "".join([f'<span class="tag-red">{k}</span>' for k in post.get('missing_keywords', [])])
            st.markdown(f"**Missing:**<br>{missing_tags_post}", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # FIT & STRATEGY EXPANDER
        with st.expander("📌 Role Fitness, Gaps & Alignment Strategy", expanded=True):
            st.write("**Fitness Summary:**", fitness.get("role_fitness_summary", ""))
            st.write("**Missing Elements & Gaps:**", fitness.get("gaps_and_missing_elements", ""))
            st.write("**Positioning Strategy:**")
            for strat in fitness.get("alignment_strategy", []):
                st.write(f"- {strat}")

        st.markdown("---")
        st.subheader("🛠️ Section Approval Controls")

        apply_summary = st.checkbox("Apply Professional Summary", value=True)
        st.info(sec2.get("professional_summary", ""))

        apply_skills = st.checkbox("Apply Categorized Skills", value=True)
        skills_grouped = sec2.get("core_competencies_grouped", {})
        for category, skills in skills_grouped.items():
            st.write(f"**{category}:** {skills}")

        apply_exp = st.checkbox("Apply Work Experience Bullets", value=True)
        for role in sec2.get("professional_experience", []):
            st.caption(f"**{role.get('role_title')}**")
            for b in role.get("bullets", []):
                st.write(f"- {b}")

        apply_projects = st.checkbox("Apply Projects Bullets", value=True)
        for proj in sec2.get("projects", []):
            st.caption(f"**{proj.get('project_title')}**")
            for b in proj.get("bullets", []):
                st.write(f"- {b}")

        # SALARY REFERENCE
        st.markdown("---")
        st.markdown("##### 🌐 Live Salary Benchmark (Verified Web Source)")
        salary_info = res.get("salary_benchmark", "No public salary data available for this company/role.")
        st.success(salary_info)

        selections = {
            "apply_summary": apply_summary,
            "apply_skills": apply_skills,
            "apply_exp": apply_exp,
            "apply_projects": apply_projects
        }

        updated_docx = build_updated_docx_inplace(
            st.session_state.get('resume_bytes', b""),
            st.session_state.get('file_type', 'pdf'),
            res,
            selections
        )

        filename = res.get("suggested_filename", "Tailored_Resume") + ".docx"

        st.download_button(
            label="📥 Download Tailored Resume (.docx)",
            data=updated_docx,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
