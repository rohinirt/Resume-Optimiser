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
    page_title="ResumeTarget | ATS Optimization", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 'Analysis'

def go_to_landing():
    st.session_state['page'] = 'landing'

# EXACT SAAS STYLING WITH CLEAN CARDS & SEGMENTED CONTROL
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
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

    .tag-green {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 3px;
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
        margin: 3px;
    }

    .panel-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 18px;
    }

    /* CUSTOMIZE SEGMENTED CONTROL TO BLUE THEME */
    div[data-testid="stSegmentedControl"] {
        background-color: #f1f5f9;
        padding: 3px;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="false"] {
        background-color: transparent !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# PAGE 1: LANDING PAGE
if st.session_state['page'] == 'landing':
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">ResumeTarget</h1>
        <p class="hero-subtitle">High-Precision ATS Optimization & Executive Resume Tailoring Engine. Built for rigorous algorithmic matching and recruiter impact.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Step 1: Provide Source Files & Target Job Description")
    
    st.markdown('<div class="upload-section-wrapper">', unsafe_allow_html=True)
    uc1, uc2, uc3, uc4 = st.columns(4)
    
    with uc1:
        uploaded_resume = st.file_uploader("Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")
    with uc2:
        uploaded_experience = st.file_uploader("Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")
    with uc3:
        uploaded_projects = st.file_uploader("Projects Repository (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")
    with uc4:
        jd_input = st.text_area("Target Job Description (JD)", height=140, placeholder="Paste job requirements...")
    
    st.markdown('</div>', unsafe_allow_html=True)

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
                st.session_state['active_tab'] = 'Analysis'
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Workflow Architecture")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("""<div class="feature-card"><div class="feature-title">Semantic Gap Analysis</div><p style="font-size:0.85rem; color:#64748b;">Evaluates technical coverage against JD requirements.</p></div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""<div class="feature-card"><div class="feature-title">Google XYZ Rewrites</div><p style="font-size:0.85rem; color:#64748b;">Restructures bullet points for quantifiable impact.</p></div>""", unsafe_allow_html=True)
    with f3:
        st.markdown("""<div class="feature-card"><div class="feature-title">Dual Sheet Previews</div><p style="font-size:0.85rem; color:#64748b;">Compare original vs optimized layout side-by-side.</p></div>""", unsafe_allow_html=True)
    with f4:
        st.markdown("""<div class="feature-card"><div class="feature-title">Executive Word Export</div><p style="font-size:0.85rem; color:#64748b;">Generates 1-page A4 formatted .docx documents.</p></div>""", unsafe_allow_html=True)

# PAGE 2: RESULTS WORKSPACE
elif st.session_state['page'] == 'results':
    
    res = st.session_state.get('results', {})
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    audit = res.get("audit_categories", {})
    fitness = res.get("fitness_and_strategy", {})

    active_tab = st.session_state.get('active_tab', 'Analysis')

    # CLEAN TOP NAVBAR HEADER: LOGO ON LEFT, SEGMENTED CONTROL & DOWNLOAD BUTTON ALIGNED ON RIGHT
    col_logo, col_toggle, col_dl = st.columns([2.5, 2.0, 1.2])
    
    with col_logo:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; padding-top: 4px;">
                <div style="background: #2563eb; color: #fff; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1rem;">R</div>
                <span style="font-size: 1.25rem; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;">ResumeTarget</span>
            </div>
        """, unsafe_allow_html=True)

    with col_toggle:
        selected_tab = st.segmented_control(
            "View Mode",
            options=["Analysis", "Optimized Resume"],
            default=active_tab,
            label_visibility="collapsed",
            key="view_segmented_control"
        )
        if selected_tab and selected_tab != active_tab:
            st.session_state['active_tab'] = selected_tab
            st.rerun()

    with col_dl:
        updated_docx = generate_new_formatted_docx(res)
        filename = res.get("suggested_filename", "Tailored_Resume") + ".docx"
        st.download_button(
            label="Download",
            data=updated_docx,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_report",
            use_container_width=True
        )

    st.markdown("<hr style='margin: 12px 0 20px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

    # EXACT 50 / 50 EQUAL SPLIT LAYOUT
    left_col, right_col = st.columns([1, 1])

    # LEFT SIDE: UPLOADED RESUME INSPECTOR (FLUSH HEADERS WITHOUT PANEL CARD WRAPPER)
    with left_col:
        hdr_l1, hdr_l2 = st.columns([2.2, 1])
        with hdr_l1:
            st.markdown(f"""
                <div style="font-weight: 800; font-size: 1.15rem; color: #0f172a;">Uploaded Resume</div>
                <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">{st.session_state.get('file_name', 'Rohini_Tembhurnikar_Resume.pdf')}</div>
            """, unsafe_allow_html=True)
        with hdr_l2:
            if st.button("Change File", on_click=go_to_landing, key="change_file_btn", use_container_width=True):
                pass
        
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        
        file_type = st.session_state.get('file_type', 'pdf')
        resume_bytes = st.session_state.get('resume_bytes', b"")
        if file_type == 'docx':
            orig_html = generate_standard_resume_sheet_html("Original Resume", resume_bytes, is_docx_file=True)
        else:
            orig_text = extract_text_from_file(st.session_state.get('upload_resume')) if 'upload_resume' in st.session_state else ""
            orig_html = generate_standard_resume_sheet_html("Original Resume", orig_text, is_docx_file=False)
            
        components.html(orig_html, height=850, scrolling=True)

    # RIGHT SIDE: ANALYSIS OR OPTIMIZED RESUME VIEW
    with right_col:
        if active_tab == 'Analysis':
            overall_score = post.get('ats_score', 86)
            st.markdown(f"""
            <div class="panel-card" style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 800; font-size: 1.15rem; color: #0f172a;">Analysis & Optimization</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">Review your resume analysis against job description requirements.</div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 12px; background: #f8fafc;">
                    <div>
                        <div style="font-size: 0.7rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Overall ATS Score</div>
                        <div style="font-size: 0.75rem; color: #16a34a; font-weight: 700;">Great Match!</div>
                    </div>
                    <div style="font-size: 1.7rem; font-weight: 800; color: #16a34a;">{overall_score} <span style="font-size: 0.85rem; color: #64748b; font-weight: 600;">/100</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            matching_kws = post.get('matching_keywords', ['SQL', 'Python', 'Tableau', 'Excel', 'Pandas', 'Power BI', 'Data Analysis', 'Statistics', 'Data Visualization', 'Looker Studio', 'BigQuery', 'ETL Pipelines'])
            tags_html = "".join([f'<span class="tag-green">✓ {k}</span>' for k in matching_kws])
            st.markdown(f"""
            <div class="panel-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: 700; font-size: 0.95rem; color: #0f172a;">Matching Skills</span>
                    <span style="background: #dcfce7; color: #15803d; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 10px;">{len(matching_kws)} Matched</span>
                </div>
                <div style="max-height: 160px; overflow-y: auto;">{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)

            missing_kws = post.get('missing_keywords', ['Machine Learning', 'Data Modeling', 'A/B Testing'])
            missing_tags = "".join([f'<span class="tag-red">✕ {k}</span>' for k in missing_kws])
            st.markdown(f"""
            <div class="panel-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-weight: 700; font-size: 0.95rem; color: #0f172a;">Missing Important Skills</span>
                    <span style="background: #fee2e2; color: #b91c1c; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 10px;">{len(missing_kws)} Missing</span>
                </div>
                <div>{missing_tags}</div>
            </div>
            """, unsafe_allow_html=True)

            strat_points = fitness.get('alignment_strategy', [
                "Highlight automated ETL data processing pipelines and record scale.",
                "Position technical competencies upfront for immediate ATS keyword weighting.",
                "Ensure bullet points strictly adhere to the Google XYZ impact formula."
            ])
            strat_items_html = "".join([f"<li style='margin-bottom: 6px;'>{strat}</li>" for strat in strat_points])
            
            st.markdown(f"""
            <div class="panel-card">
                <div style="font-weight: 800; font-size: 1rem; color: #0f172a; margin-bottom: 10px;">Job Compatibility & Alignment Strategy</div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.5; margin-bottom: 8px;">
                    <strong>Role Fitness Summary:</strong> {fitness.get('role_fitness_summary', 'Strong analytical foundation matching core technical requirements.')}
                </div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.5; margin-bottom: 12px;">
                    <strong>Gaps & Missing Elements:</strong> {fitness.get('gaps_and_missing_elements', 'Minor gaps in advanced secondary cloud workflows.')}
                </div>
                <div style="font-weight: 700; font-size: 0.88rem; color: #0f172a; margin-bottom: 6px;">Strategic Alignment Roadmap:</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.85rem; color: #64748b; line-height: 1.5;">
                    {strat_items_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)

        else:
            paper_html = generate_paper_sheet_tailored_html(res)
            components.html(paper_html, height=880, scrolling=True)

    st.markdown("<br>", unsafe_allow_html=True)
