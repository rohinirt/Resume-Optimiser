import streamlit as st
from utils import (
    extract_text_from_file, 
    get_pdf_preview_html, 
    get_docx_preview_text, 
    generate_highlighted_optimized_html,
    build_updated_docx_inplace
)
from agent_engine import analyze_and_optimize_resume, fetch_real_web_salary

st.set_page_config(
    page_title="ResumeAI Pro | Executive ATS Tailor", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# REMOVE DEFAULT STREAMLIT TOP MARGINS & APPLY EXECUTIVE THEME
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* REMOVE TOP MARGIN PADDING */
    .block-container {
        padding-top: 1rem !important;
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
    
    /* EXECUTIVE NAVIGATION BANNER */
    .executive-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-sub {
        color: #94a3b8;
        margin-top: 4px;
        font-size: 0.95rem;
    }

    /* CARD CONTAINERS */
    .card-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* CUSTOM BADGES */
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

    /* PRIMARY CTA BUTTON */
    div.stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.45) !important;
    }
</style>
""", unsafe_allow_html=True)

# HERO TOP BANNER (ATTACHED TO VERY TOP)
st.markdown("""
<div class="executive-hero">
    <div>
        <h1 class="hero-title">⚡ ResumeAI Pro</h1>
        <p class="hero-sub">AI-Powered ATS Optimization, Real-Time Market Search & In-Place Document Formatting</p>
    </div>
    <div style="text-align: right; font-size: 0.85rem; color: #cbd5e1;">
        <span style="background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px;">v2.5 Gemini Engine</span>
    </div>
</div>
""", unsafe_allow_html=True)

# STEP 1: INPUT CONTAINER
st.markdown("##### 📥 Step 1: Upload Documents & Job Description")

col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])

with col1:
    uploaded_resume = st.file_uploader("1. Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")

with col2:
    uploaded_experience = st.file_uploader("2. Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")

with col3:
    uploaded_projects = st.file_uploader("3. Projects File (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")

with col4:
    jd_input = st.text_area("4. Target Job Description (JD)", height=120, placeholder="Paste job description keywords, tools, and responsibilities...")

st.markdown("<br>", unsafe_allow_html=True)
analyze_btn = st.button("🚀 Analyze, Align & Optimize Resume", type="primary", use_container_width=True)

if analyze_btn and uploaded_resume and jd_input:
    with st.spinner("Processing documents, performing semantic ATS analysis, and running live salary search..."):
        file_bytes = uploaded_resume.read()
        uploaded_resume.seek(0)
        st.session_state['resume_bytes'] = file_bytes
        st.session_state['file_type'] = uploaded_resume.name.split(".")[-1].lower()
        
        # Extract inputs
        resume_text = extract_text_from_file(uploaded_resume)
        experience_text = extract_text_from_file(uploaded_experience) if uploaded_experience else ""
        projects_text = extract_text_from_file(uploaded_projects) if uploaded_projects else ""
        
        # Analyze via Gemini AI
        results = analyze_and_optimize_resume(resume_text, projects_text, experience_text, jd_input)
        
        # Fetch Web Salary via Search Grounding
        filename_parts = results.get("suggested_filename", "").split("_")
        company_name = filename_parts[-1] if len(filename_parts) > 1 else ""
        real_salary = fetch_real_web_salary(company_name, "Data Analyst")
        results["salary_benchmark"] = real_salary

        st.session_state['results'] = results

st.markdown("---")

# STEP 2: TABBED EXECUTIVE DASHBOARD
if 'results' in st.session_state:
    res = st.session_state['results']
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    fitness = res.get("fitness_and_strategy", {})
    sec2 = res.get("section_2_tailored_content", {})

    st.markdown("##### 📊 Step 2: Optimization Analytics & Side-by-Side Comparison")

    tab_overview, tab_comparison, tab_editor = st.tabs([
        "📈 Match Metrics & Strategy", 
        "📄 Side-by-Side Resume Comparison", 
        "🛠️ Section Editor & Export"
    ])

    # TAB 1: METRICS & STRATEGY
    with tab_overview:
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown('<div class="card-box">', unsafe_allow_html=True)
            st.subheader("🎯 ATS Match Delta")
            m1, m2 = st.columns(2)
            m1.metric("Pre-ATS Score", f"{pre.get('ats_score', 0)}%")
            m2.metric("Post-ATS Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")
            
            st.markdown("---")
            st.markdown("###### Keywords Analysis")
            k1, k2 = st.columns(2)
            with k1:
                st.write("**Pre-Matching:**")
                st.markdown("".join([f'<span class="tag-green">{k}</span>' for k in pre.get('matching_keywords', [])]), unsafe_allow_html=True)
                st.write("**Pre-Missing:**")
                st.markdown("".join([f'<span class="tag-red">{k}</span>' for k in pre.get('missing_keywords', [])]), unsafe_allow_html=True)
            with k2:
                st.write("**Post-Matching:**")
                st.markdown("".join([f'<span class="tag-green">{k}</span>' for k in post.get('matching_keywords', [])]), unsafe_allow_html=True)
                st.write("**Post-Missing:**")
                st.markdown("".join([f'<span class="tag-red">{k}</span>' for k in post.get('missing_keywords', [])]), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="card-box">', unsafe_allow_html=True)
            st.subheader("📌 Role Fitness & Positioning Strategy")
            st.write("**Fitness Summary:**", fitness.get("role_fitness_summary", ""))
            st.write("**Gaps & Missing Elements:**", fitness.get("gaps_and_missing_elements", ""))
            st.write("**Alignment Positioning Strategy:**")
            for strat in fitness.get("alignment_strategy", []):
                st.write(f"- {strat}")
                
            st.markdown("---")
            st.markdown("###### 🌐 Live Web Search Salary Reference")
            st.success(res.get("salary_benchmark", "No public salary data available."))
            st.markdown('</div>', unsafe_allow_html=True)

    # TAB 2: SIDE-BY-SIDE COMPARISON (ORIGINAL VS OPTIMIZED HIGHLIGHTS)
    with tab_comparison:
        view_left, view_right = st.columns([1, 1])

        with view_left:
            st.subheader("👁️ Original Master Resume")
            if st.session_state.get('file_type') == 'pdf':
                st.markdown(get_pdf_preview_html(st.session_state['resume_bytes'], height=750), unsafe_allow_html=True)
            else:
                text_preview = get_docx_preview_text(uploaded_resume) if uploaded_resume else ""
                st.text_area("Document Text Stream", text_preview, height=750, disabled=True)

        with view_right:
            st.subheader("✨ Optimized Resume (Changes Highlighted)")
            opt_html = generate_highlighted_optimized_html(res)
            st.markdown(opt_html, unsafe_allow_html=True)

    # TAB 3: EDITOR & DOWNLOAD CONTROLS
    with tab_editor:
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.subheader("🛠️ Approve Sections to Merge into Word Document")

        apply_summary = st.checkbox("Apply Tailored Professional Summary", value=True)
        st.info(sec2.get("professional_summary", ""))

        apply_skills = st.checkbox("Apply Categorized Skills", value=True)
        skills_grouped = sec2.get("core_competencies_grouped", {})
        for category, skills in skills_grouped.items():
            st.write(f"**{category}:** {skills}")

        apply_exp = st.checkbox("Apply Google XYZ Experience Bullets", value=True)
        for role in sec2.get("professional_experience", []):
            st.caption(f"**{role.get('role_title')}**")
            for b in role.get("bullets", []):
                st.write(f"- {b}")

        apply_projects = st.checkbox("Apply Selected Projects Bullets", value=True)
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
            label="📥 Download Updated Resume (.docx)",
            data=updated_docx,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
