import streamlit as st
from utils import (
    extract_text_from_file, 
    get_pdf_preview_html, 
    get_docx_preview_html, 
    generate_paper_sheet_tailored_html,
    build_updated_docx_inplace
)
from agent_engine import analyze_and_optimize_resume, fetch_real_web_salary

st.set_page_config(
    page_title="ResumeAI Pro | Targeted ATS Optimizer", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

def go_to_results():
    st.session_state['page'] = 'results'

def go_to_landing():
    st.session_state['page'] = 'landing'

# MODERN WEB APPLICATION CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 40px;
        border-radius: 20px;
        color: #ffffff;
        margin-bottom: 28px;
        box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.2);
        text-align: center;
    }
    
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 12px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.15rem;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.6;
    }

    .feature-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .feature-icon {
        font-size: 1.8rem;
        margin-bottom: 8px;
    }

    .tag-green {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }
    
    .tag-red {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.45) !important;
    }
</style>
""", unsafe_allow_html=True)

# PAGE 1: LANDING PAGE
if st.session_state['page'] == 'landing':
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">Target Your Resume For Any Job Description</h1>
        <p class="hero-subtitle">Optimize your master resume against target job requirements, match ATS keywords, highlight Google XYZ metrics, and verify salary benchmarks in seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### ⚡ What Happens After You Upload?")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("""<div class="feature-card"><div class="feature-icon">🔍</div><strong>1. ATS Gap Analysis</strong><p style="font-size:0.82rem; color:#64748b; margin-top:4px;">Extracts required tools & calculates pre/post match scores.</p></div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""<div class="feature-card"><div class="feature-icon">📝</div><strong>2. Google XYZ Rewrites</strong><p style="font-size:0.82rem; color:#64748b; margin-top:4px;">Restructures experience bullets using action verbs & metrics.</p></div>""", unsafe_allow_html=True)
    with f3:
        st.markdown("""<div class="feature-card"><div class="feature-icon">👁️</div><strong>3. Side-by-Side View</strong><p style="font-size:0.82rem; color:#64748b; margin-top:4px;">Compare original document vs highlighted paper preview.</p></div>""", unsafe_allow_html=True)
    with f4:
        st.markdown("""<div class="feature-card"><div class="feature-icon">🌐</div><strong>4. Live Search & Export</strong><p style="font-size:0.82rem; color:#64748b; margin-top:4px;">Searches real web salary data & exports in-place formatted .docx.</p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📥 Step 1: Upload Files & Target Job Description")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])

    with col1:
        uploaded_resume = st.file_uploader("1. Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")

    with col2:
        uploaded_experience = st.file_uploader("2. Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")

    with col3:
        uploaded_projects = st.file_uploader("3. Projects Repository (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")

    with col4:
        jd_input = st.text_area("4. Target Job Description (JD)", height=130, placeholder="Paste target job responsibilities and requirements...")

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("✨ Target Resume & Launch Results Workspace", type="primary", use_container_width=True)

    if analyze_btn:
        if not uploaded_resume or not jd_input:
            st.warning("Please upload a Master Resume and paste a Job Description to proceed.")
        else:
            with st.spinner("Extracting documents, parsing keywords, and tailoring your resume..."):
                file_bytes = uploaded_resume.read()
                uploaded_resume.seek(0)
                st.session_state['resume_bytes'] = file_bytes
                st.session_state['file_type'] = uploaded_resume.name.split(".")[-1].lower()
                st.session_state['file_name'] = uploaded_resume.name
                
                resume_text = extract_text_from_file(uploaded_resume)
                experience_text = extract_text_from_file(uploaded_experience) if uploaded_experience else ""
                projects_text = extract_text_from_file(uploaded_projects) if uploaded_projects else ""
                
                results = analyze_and_optimize_resume(resume_text, projects_text, experience_text, jd_input)
                
                filename_parts = results.get("suggested_filename", "").split("_")
                company_name = filename_parts[-1] if len(filename_parts) > 1 else ""
                real_salary = fetch_real_web_salary(company_name, "Data Analyst")
                results["salary_benchmark"] = real_salary

                st.session_state['results'] = results
                st.session_state['page'] = 'results'
                st.rerun()

# PAGE 2: RESULTS WORKSPACE
elif st.session_state['page'] == 'results':
    
    nav_col1, nav_col2 = st.columns([1, 6])
    with nav_col1:
        st.button("⬅️ Back to Uploads", on_click=go_to_landing, use_container_width=True)
    with nav_col2:
        st.markdown("<h2 style='margin:0; font-weight:800; color:#0f172a;'>🎯 Resume Optimization Workspace</h2>", unsafe_allow_html=True)

    st.markdown("---")

    res = st.session_state.get('results', {})
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    fitness = res.get("fitness_and_strategy", {})
    sec2 = res.get("section_2_tailored_content", {})

    # METRICS ROW
    m_col1, m_col2 = st.columns([1, 1])

    with m_col1:
        st.markdown('<div style="background:#ffffff; border:1px solid #e2e8f0; padding:20px; border-radius:12px;">', unsafe_allow_html=True)
        st.subheader("📊 Match Score & Keywords")
        sc1, sc2 = st.columns(2)
        sc1.metric("Pre-ATS Score", f"{pre.get('ats_score', 0)}%")
        sc2.metric("Post-ATS Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")
        
        st.markdown("---")
        k1, k2 = st.columns(2)
        with k1:
            st.write("**Pre-Matching Keywords:**")
            st.markdown("".join([f'<span class="tag-green">{k}</span>' for k in pre.get('matching_keywords', [])]), unsafe_allow_html=True)
            st.write("**Pre-Missing Keywords:**")
            st.markdown("".join([f'<span class="tag-red">{k}</span>' for k in pre.get('missing_keywords', [])]), unsafe_allow_html=True)
        with k2:
            st.write("**Post-Matching Keywords:**")
            st.markdown("".join([f'<span class="tag-green">{k}</span>' for k in post.get('matching_keywords', [])]), unsafe_allow_html=True)
            st.write("**Post-Missing Keywords:**")
            st.markdown("".join([f'<span class="tag-red">{k}</span>' for k in post.get('missing_keywords', [])]), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with m_col2:
        st.markdown('<div style="background:#ffffff; border:1px solid #e2e8f0; padding:20px; border-radius:12px;">', unsafe_allow_html=True)
        st.subheader("📌 Role Fitness & Strategy")
        st.write("**Fitness Summary:**", fitness.get("role_fitness_summary", ""))
        st.write("**Missing Elements & Gaps:**", fitness.get("gaps_and_missing_elements", ""))
        st.write("**Alignment Positioning Strategy:**")
        for strat in fitness.get("alignment_strategy", []):
            st.write(f"- {strat}")
            
        st.markdown("---")
        st.markdown("###### 🌐 Live Web Search Salary Reference")
        st.success(res.get("salary_benchmark", "No public salary data available."))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # SIDE BY SIDE RESUME VIEWERS (FIXED HTML RENDERING)
    st.markdown("### 📄 Side-by-Side Resume Viewers")
    view_left, view_right = st.columns([1, 1])

    with view_left:
        st.markdown("##### 👁️ Original Master Resume")
        file_type = st.session_state.get('file_type', 'pdf')
        resume_bytes = st.session_state.get('resume_bytes', b"")
        
        if file_type == 'pdf':
            pdf_html = get_pdf_preview_html(resume_bytes, height=800)
            st.markdown(pdf_html, unsafe_allow_html=True)
        else:
            docx_html = get_docx_preview_html(resume_bytes, height=800)
            st.markdown(docx_html, unsafe_allow_html=True)

    with view_right:
        st.markdown("##### ✨ Tailored Resume Sheet (Highlights Applied)")
        paper_html = generate_paper_sheet_tailored_html(res)
        # CRITICAL FIX: Explicitly render compiled HTML
        st.markdown(paper_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION EDITOR & EXPORT TOOLBAR
    st.markdown("### 🛠️ Section Editor & Export Content")
    st.markdown('<div style="background:#ffffff; border:1px solid #e2e8f0; padding:24px; border-radius:12px;">', unsafe_allow_html=True)

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

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Tailored Resume (.docx)",
        data=updated_docx,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
