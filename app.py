import streamlit as st
import streamlit.components.v1 as components
from utils import (
    extract_text_from_file, 
    generate_standard_resume_sheet_html,
    generate_paper_sheet_tailored_html,
    generate_new_formatted_docx
)
from agent_engine import analyze_and_optimize_resume, fetch_real_web_salary

st.set_page_config(
    page_title="ResumeForge AI | Targeted ATS Optimizer", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

def go_to_landing():
    st.session_state['page'] = 'landing'

# MODERN APP STYLING & COLOR PALETTE (NO EMOJIS)
# MODERN LIGHT THEME APP STYLING
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* SWITCHED TO CLEAN LIGHT THEME */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #f1f5f9 100%, #e2e8f0 0%);
        padding: 42px;
        border-radius: 20px;
        color: #0f172a;
        margin-bottom: 28px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1.5px;
        margin-bottom: 12px;
        background: linear-gradient(90deg, #0284c7 0%, #4f46e5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #475569;
        font-size: 1.15rem;
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* LARGER, DISTINCT UPLOAD CARDS WITH ATTRACTIVE COLORS */
    .upload-card-custom {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 6px 15px -3px rgba(0, 0, 0, 0.05);
        min-height: 210px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .upload-card-custom:hover {
        border-color: #2563eb;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
    }

    .feature-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    
    .feature-title {
        color: #0284c7;
        font-weight: 700;
        font-size: 1.05rem;
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

    div.stDownloadButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
</style>
""", unsafe_allow_html=True)

# PAGE 1: LANDING PAGE
if st.session_state['page'] == 'landing':
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">ResumeForge AI</h1>
        <p class="hero-subtitle">High-Precision ATS Optimization & Executive Resume Tailoring Engine. Built for rigorous algorithmic matching and recruiter impact.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Step 1: Provide Source Files & Target Job Description")
    
    # LARGER COLORED UPLOAD CARDS WRAPPER
    uc1, uc2, uc3, uc4 = st.columns(4)
    
    with uc1:
        st.markdown('<div class="upload-card-custom">', unsafe_allow_html=True)
        uploaded_resume = st.file_uploader("Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with uc2:
        st.markdown('<div class="upload-card-custom">', unsafe_allow_html=True)
        uploaded_experience = st.file_uploader("Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with uc3:
        st.markdown('<div class="upload-card-custom">', unsafe_allow_html=True)
        uploaded_projects = st.file_uploader("Projects Repository (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with uc4:
        st.markdown('<div class="upload-card-custom" style="padding: 15px;">', unsafe_allow_html=True)
        jd_input = st.text_area("Target Job Description (JD)", height=135, placeholder="Paste job requirements...")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("Initialize ATS Audit & Tailoring Workspace", type="primary", use_container_width=True)

    if analyze_btn:
        if not uploaded_resume or not jd_input:
            st.warning("Please upload a Master Resume and paste a Job Description to proceed.")
        else:
            with st.spinner("Executing semantic keyword mapping, gap analysis, and layout generation..."):
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Workflow Architecture")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("""<div class="feature-card"><div class="feature-title">Semantic Gap Analysis</div><p style="font-size:0.85rem; color:#94a3b8;">Evaluates technical coverage against JD requirements.</p></div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""<div class="feature-card"><div class="feature-title">Google XYZ Rewrites</div><p style="font-size:0.85rem; color:#94a3b8;">Restructures bullet points for quantifiable impact.</p></div>""", unsafe_allow_html=True)
    with f3:
        st.markdown("""<div class="feature-card"><div class="feature-title">Dual Sheet Previews</div><p style="font-size:0.85rem; color:#94a3b8;">Compare original vs optimized layout side-by-side.</p></div>""", unsafe_allow_html=True)
    with f4:
        st.markdown("""<div class="feature-card"><div class="feature-title">Executive Word Export</div><p style="font-size:0.85rem; color:#94a3b8;">Generates 1-page A4 formatted .docx documents.</p></div>""", unsafe_allow_html=True)

# PAGE 2: RESULTS WORKSPACE
elif st.session_state['page'] == 'results':
    
    nav_col1, nav_col2 = st.columns([1, 6])
    with nav_col1:
        st.button("Back to Uploads", on_click=go_to_landing, use_container_width=True)
    with nav_col2:
        st.markdown("<h2 style='margin:0; font-weight:800; color:#f8fafc;'>Resume Optimization Workspace</h2>", unsafe_allow_html=True)

    st.markdown("---")

    res = st.session_state.get('results', {})
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    audit = res.get("audit_categories", {})
    fitness = res.get("fitness_and_strategy", {})

    # METRICS & TRANSPARENT AUDIT DASHBOARD
    m_col1, m_col2 = st.columns([1, 1])

    with m_col1:
        st.markdown('<div style="background:#1e293b; border:1px solid #334155; padding:24px; border-radius:12px;">', unsafe_allow_html=True)
        st.subheader("ATS Score & Keyword Audit")
        
        sc1, sc2 = st.columns(2)
        sc1.metric("Pre-Optimization Score", f"{pre.get('ats_score', 0)}%")
        sc2.metric("Post-Optimization Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")
        
        st.markdown("---")
        
        # KEYWORD PILLS
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
        st.markdown('<div style="background:#1e293b; border:1px solid #334155; padding:24px; border-radius:12px;">', unsafe_allow_html=True)
        st.subheader("Granular Audit Breakdown")
        
        # 5 AUDIT CATEGORIES DISPLAY
        audit_mapping = [
            ("Hard Skills & Keyword Match (40%)", audit.get("hard_skills", {})),
            ("Formatting & Parsability (15%)", audit.get("formatting", {})),
            ("Impact & Metrics / Google XYZ (25%)", audit.get("impact_metrics", {})),
            ("Length & Brevity (10%)", audit.get("length_brevity", {})),
            ("Section Completeness (10%)", audit.get("section_completeness", {}))
        ]
        
        for cat_name, data in audit_mapping:
            score_val = data.get("score", 80)
            st.write(f"**{cat_name}** — Score: `{score_val}%`")
            st.progress(score_val)
            st.caption(f"Feedback: {data.get('feedback', '')}")
            fixes = data.get("actionable_fixes", [])
            if fixes:
                st.caption(f"Actionable Fix: {fixes[0]}")
            st.markdown("---")
            
        # TOGGLE FOR ORIGINAL ROLE FITNESS & ALIGNMENT STRATEGY
        with st.expander("Show Original Role Fitness & Alignment Strategy"):
            st.write("**Fitness Summary:**", fitness.get("role_fitness_summary", ""))
            st.write("**Gaps & Missing Elements:**", fitness.get("gaps_and_missing_elements", ""))
            st.write("**Alignment Positioning Strategy:**")
            for strat in fitness.get("alignment_strategy", []):
                st.write(f"- {strat}")
                
        st.markdown("###### Live Web Search Salary Reference")
        st.success(res.get("salary_benchmark", "No public salary data available."))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # SIDE BY SIDE RESUME VIEWERS
    st.markdown("### Side-by-Side Resume Viewers")
    view_left, view_right = st.columns([1, 1])

    with view_left:
        st.markdown("##### Master Resume (Source View)")
        file_type = st.session_state.get('file_type', 'pdf')
        resume_bytes = st.session_state.get('resume_bytes', b"")
        
        if file_type == 'docx':
            orig_html = generate_standard_resume_sheet_html("Original Resume", resume_bytes, is_docx_file=True)
        else:
            orig_text = extract_text_from_file(st.session_state.get('upload_resume')) if 'upload_resume' in st.session_state else ""
            orig_html = generate_standard_resume_sheet_html("Original Resume", orig_text, is_docx_file=False)
            
        components.html(orig_html, height=1050, scrolling=True)

    with view_right:
        hdr_col1, hdr_col2 = st.columns([1.5, 1])
        with hdr_col1:
            st.markdown("##### Tailored Resume Preview")
        with hdr_col2:
            updated_docx = generate_new_formatted_docx(res)
            filename = res.get("suggested_filename", "Tailored_Resume") + ".docx"
            st.download_button(
                label="Download Optimized Resume (.docx)",
                data=updated_docx,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_top_right",
                use_container_width=True
            )

        paper_html = generate_paper_sheet_tailored_html(res)
        components.html(paper_html, height=1050, scrolling=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # SUMMARY OF CHANGES
    st.markdown("### Summary of Key Resume Enhancements")
    st.markdown('<div style="background:#1e293b; border:1px solid #334155; padding:24px; border-radius:12px;">', unsafe_allow_html=True)
    
    changes = res.get("summary_of_changes", [
        "Aligned technical competencies directly with job description requirements.",
        "Restructured experience bullets using Google XYZ formula to highlight metrics.",
        "Optimized layout geometry to ensure compliance with 1-page A4 constraints."
    ])
    
    for idx, change in enumerate(changes, 1):
        st.markdown(f"**{idx}.** {change}")

    st.markdown('</div>', unsafe_allow_html=True)
