import streamlit as st
from utils import (
    extract_text_from_file, 
    get_pdf_preview_html, 
    get_docx_preview_text, 
    build_updated_docx_inplace
)
from agent_engine import analyze_and_optimize_resume, fetch_real_web_salary

st.set_page_config(
    page_title="ResumeAI Pro | Next-Gen ATS Optimizer", 
    page_icon="⚡", 
    layout="wide"
)

# MODERN CUSTOM CSS FOR LUXURY UI LOOK
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        color: #f0f6fc;
    }
    
    .glass-card {
        background: rgba(22, 27, 34, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }
    
    .keyword-badge-green {
        background-color: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 3px;
        font-weight: 500;
    }
    
    .keyword-badge-red {
        background-color: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid rgba(248, 81, 73, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 3px;
        font-weight: 500;
    }
    
    div.stButton > button {
        background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(46, 160, 67, 0.39);
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(46, 160, 67, 0.55);
    }
</style>
""", unsafe_allow_html=True)

# NAVBAR HEADER
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 30px;">
    <div>
        <h1 style="margin: 0; font-size: 2.2rem; background: linear-gradient(90deg, #58a6ff, #bc8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚡ ResumeAI Tailor Pro</h1>
        <p style="margin: 5px 0 0 0; color: #8b949e;">Enterprise-grade ATS alignment and real-time live market benchmarking.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ROW 1: INPUT FILES
st.markdown("### 📥 1. Document Uploads & Target Job")
col1, col2, col3, col4 = st.columns(4)

with col1:
    uploaded_resume = st.file_uploader("1. Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")

with col2:
    uploaded_experience = st.file_uploader("2. Work Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")

with col3:
    uploaded_projects = st.file_uploader("3. Projects Repository File (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")

with col4:
    jd_input = st.text_area("4. Job Description (JD)", height=130, placeholder="Paste JD requirements here...")

analyze_btn = st.button("🚀 Optimize & Align Resume", type="primary", use_container_width=True)

if analyze_btn and uploaded_resume and jd_input:
    with st.spinner("Analyzing keyword coverage, running Google search grounding for salary, and tailoring resume..."):
        file_bytes = uploaded_resume.read()
        uploaded_resume.seek(0)
        st.session_state['resume_bytes'] = file_bytes
        st.session_state['file_type'] = uploaded_resume.name.split(".")[-1].lower()
        
        # Parse inputs
        resume_text = extract_text_from_file(uploaded_resume)
        experience_text = extract_text_from_file(uploaded_experience) if uploaded_experience else ""
        projects_text = extract_text_from_file(uploaded_projects) if uploaded_projects else ""
        
        # Call ATS Optimization Agent
        results = analyze_and_optimize_resume(resume_text, projects_text, experience_text, jd_input)
        
        # Fetch Real Web Grounded Salary Data
        filename_parts = results.get("suggested_filename", "").split("_")
        company_name = filename_parts[-1] if len(filename_parts) > 1 else ""
        real_salary = fetch_real_web_salary(company_name, "Data Analyst")
        results["salary_benchmark"] = real_salary

        st.session_state['results'] = results

st.markdown("---")

# ROW 2: DASHBOARD & PREVIEW
if 'results' in st.session_state:
    res = st.session_state['results']
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    fitness = res.get("fitness_and_strategy", {})
    sec2 = res.get("section_2_tailored_content", {})

    col_left, col_right = st.columns([1, 1])

    # LEFT COLUMN: LIVE RESUME PREVIEW
    with col_left:
        st.subheader("👁️ Live Master Resume View")
        if st.session_state.get('file_type') == 'pdf':
            st.markdown(get_pdf_preview_html(st.session_state['resume_bytes']), unsafe_allow_html=True)
        else:
            text_preview = get_docx_preview_text(uploaded_resume) if uploaded_resume else ""
            st.text_area("Document View", text_preview, height=700, disabled=True)

    # RIGHT COLUMN: ANALYTICS DASHBOARD
    with col_right:
        st.subheader("📊 Optimization Dashboard")

        # METRICS CARDS
        m1, m2 = st.columns(2)
        m1.metric("Pre-ATS Match Score", f"{pre.get('ats_score', 0)}%")
        m2.metric("Post-ATS Match Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")

        # BADGES DISPLAY FOR KEYWORDS
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.markdown("##### 🔴 Pre-Optimization Keywords")
            m_tags = "".join([f'<span class="keyword-badge-green">{k}</span>' for k in pre.get('matching_keywords', [])])
            st.markdown(f"**Matching:**<br>{m_tags}", unsafe_allow_html=True)
            
            missing_tags = "".join([f'<span class="keyword-badge-red">{k}</span>' for k in pre.get('missing_keywords', [])])
            st.markdown(f"**Missing:**<br>{missing_tags}", unsafe_allow_html=True)

        with k_col2:
            st.markdown("##### 🟢 Post-Optimization Keywords")
            m_tags_post = "".join([f'<span class="keyword-badge-green">{k}</span>' for k in post.get('matching_keywords', [])])
            st.markdown(f"**Matching:**<br>{m_tags_post}", unsafe_allow_html=True)
            
            missing_tags_post = "".join([f'<span class="keyword-badge-red">{k}</span>' for k in post.get('missing_keywords', [])])
            st.markdown(f"**Missing:**<br>{missing_tags_post}", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ROLE FITNESS & STRATEGY
        with st.expander("📌 Role Fitness & Positioning Strategy", expanded=True):
            st.write("**Fitness Assessment:**", fitness.get("role_fitness_summary", ""))
            st.write("**Gaps & Missing Elements:**", fitness.get("gaps_and_missing_elements", ""))
            st.write("**Positioning Strategy:**")
            for strat in fitness.get("alignment_strategy", []):
                st.write(f"- {strat}")

        st.markdown("---")
        st.subheader("🛠️ Approve Sections to Apply")

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

        # REAL INTERNET SALARY BENCHMARK RESULT
        st.markdown("---")
        st.markdown("##### 🌐 Live Web Search Salary Benchmark")
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
