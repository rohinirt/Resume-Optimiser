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

# MODERN MAROON & PINK LUXURY THEME STYLING MATCHING TARGET REFERENCE
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 96% !important;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #831843 0%, #500724 100%);
        padding: 48px;
        border-radius: 24px;
        color: #ffffff;
        margin-bottom: 32px;
        box-shadow: 0 20px 40px -15px rgba(131, 24, 67, 0.3);
        text-align: center;
    }
    
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -1.5px;
        margin-bottom: 12px;
        color: #fff1f2;
    }

    .hero-subtitle {
        color: #fbcfe8;
        font-size: 1.15rem;
        max-width: 750px;
        margin: 0 auto;
        line-height: 1.6;
    }

    .upload-section-wrapper {
        background: #ffffff;
        border: 2px solid #fbcfe8;
        padding: 32px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(131, 24, 67, 0.05);
        margin-bottom: 35px;
    }

    .feature-card {
        background: #ffffff;
        border: 1px solid #fbcfe8;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(131, 24, 67, 0.04);
    }
    
    .feature-title {
        color: #831843;
        font-weight: 700;
        font-size: 1.1rem;
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

    /* TOP NAVBAR HEADER CARD */
    .top-navbar {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 14px 24px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    div.stDownloadButton > button {
        background: #ffffff !important;
        color: #500724 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #831843 0%, #500724 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(131, 24, 67, 0.2) !important;
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
        st.markdown("""<div class="feature-card"><div class="feature-title">Semantic Gap Analysis</div><p style="font-size:0.85rem; color:#881337;">Evaluates technical coverage against JD requirements.</p></div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""<div class="feature-card"><div class="feature-title">Google XYZ Rewrites</div><p style="font-size:0.85rem; color:#881337;">Restructures bullet points for quantifiable impact.</p></div>""", unsafe_allow_html=True)
    with f3:
        st.markdown("""<div class="feature-card"><div class="feature-title">Dual Sheet Previews</div><p style="font-size:0.85rem; color:#881337;">Compare original vs optimized layout side-by-side.</p></div>""", unsafe_allow_html=True)
    with f4:
        st.markdown("""<div class="feature-card"><div class="feature-title">Executive Word Export</div><p style="font-size:0.85rem; color:#881337;">Generates 1-page A4 formatted .docx documents.</p></div>""", unsafe_allow_html=True)

# PAGE 2: RESULTS WORKSPACE WITH TOP NAVBAR & TOGGLE
elif st.session_state['page'] == 'results':
    
    res = st.session_state.get('results', {})
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    audit = res.get("audit_categories", {})
    fitness = res.get("fitness_and_strategy", {})

    # TOP NAVBAR HEADER MATCHING REFERENCE
    col_logo, col_tabs, col_dl = st.columns([1.5, 2, 1.2])
    with col_logo:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; padding-top: 6px;">
                <div style="background: linear-gradient(135deg, #831843 0%, #500724 100%); color: #fff; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem;">R</div>
                <span style="font-size: 1.3rem; font-weight: 800; color: #500724; letter-spacing: -0.5px;">ResumeTarget</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col_tabs:
        t1, t2 = st.columns(2)
        with t1:
            if st.button("Analysis", use_container_width=True, key="tab_analysis"):
                st.session_state['active_tab'] = 'Analysis'
                st.rerun()
        with t2:
            if st.button("Optimized Resume", use_container_width=True, key="tab_optimized"):
                st.session_state['active_tab'] = 'Optimized Resume'
                st.rerun()

    with col_dl:
        updated_docx = generate_new_formatted_docx(res)
        filename = res.get("suggested_filename", "Tailored_Resume") + ".docx"
        st.download_button(
            label="Download Analysis Report",
            data=updated_docx,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_report",
            use_container_width=True
        )

    st.markdown("<hr style='margin: 10px 0 20px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

    # MAIN SPLIT LAYOUT
    left_col, right_col = st.columns([1.1, 1.9])

    # LEFT SIDE: UPLOADED RESUME INSPECTOR
    with left_col:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 20px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a;">Uploaded Resume</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">%s</div>
                </div>
        """ % st.session_state.get('file_name', 'Rohini_Tembhurnikar_Resume.pdf'), unsafe_allow_html=True)
        
        if st.button("Change File", on_click=go_to_landing, key="change_file_btn"):
            pass
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        file_type = st.session_state.get('file_type', 'pdf')
        resume_bytes = st.session_state.get('resume_bytes', b"")
        if file_type == 'docx':
            orig_html = generate_standard_resume_sheet_html("Original Resume", resume_bytes, is_docx_file=True)
        else:
            orig_text = extract_text_from_file(st.session_state.get('upload_resume')) if 'upload_resume' in st.session_state else ""
            orig_html = generate_standard_resume_sheet_html("Original Resume", orig_text, is_docx_file=False)
            
        components.html(orig_html, height=880, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT SIDE: DYNAMIC TAB VIEW (ANALYSIS VS OPTIMIZED RESUME)
    with right_col:
        active_tab = st.session_state.get('active_tab', 'Analysis')

        if active_tab == 'Analysis':
            # TOP SUMMARY BOX WITH OVERALL ATS SCORE
            overall_score = post.get('ats_score', 86)
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 24px; border-radius: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                <div>
                    <div style="font-weight: 800; font-size: 1.2rem; color: #0f172a;">Analysis & Optimization</div>
                    <div style="font-size: 0.88rem; color: #64748b; margin-top: 2px;">Review your resume analysis or view the optimized resume.</div>
                </div>
                <div style="display: flex; align-items: center; gap: 16px; border: 1px solid #e2e8f0; padding: 10px 18px; border-radius: 12px; background: #f8fafc;">
                    <div>
                        <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Overall ATS Score</div>
                        <div style="font-size: 0.75rem; color: #16a34a; font-weight: 700; margin-top: 2px;">Great Match!</div>
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #16a34a;">{overall_score} <span style="font-size: 0.9rem; color: #64748b; font-weight: 600;">/100</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # TWO COLUMN BREAKDOWN GRID (MATCHING REFERENCE IMAGE)
            g_col1, g_col2 = st.columns(2)

            with g_col1:
                # Top Matching Skills Box
                matching_kws = post.get('matching_keywords', ['SQL', 'Python', 'Tableau', 'Excel', 'Pandas', 'Power BI', 'Data Analysis', 'Statistics', 'Data Visualization', 'Looker Studio'])
                tags_html = "".join([f'<span class="tag-green">&#10003; {k}</span>' for k in matching_kws[:10]])
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 20px; border-radius: 16px; min-height: 220px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-weight: 700; font-size: 1rem; color: #0f172a;">Top Matching Skills</span>
                        <span style="background: #dcfce7; color: #15803d; font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;">{len(matching_kws)} Matched</span>
                    </div>
                    <div style="margin-top: 10px;">{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)

                # Missing Important Skills Box
                missing_kws = post.get('missing_keywords', ['Machine Learning', 'Data Modeling', 'BigQuery', 'Looker', 'A/B Testing'])
                missing_tags = "".join([f'<span class="tag-red">&#10005; {k}</span>' for k in missing_kws])
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 20px; border-radius: 16px; min-height: 200px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="font-weight: 700; font-size: 1rem; color: #0f172a;">Missing Important Skills</span>
                        <span style="background: #fee2e2; color: #b91c1c; font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;">{len(missing_kws)} Missing</span>
                    </div>
                    <div style="margin-top: 10px;">{missing_tags}</div>
                </div>
                """, unsafe_allow_html=True)

            with g_col2:
                # Match Breakdown Box
                st.markdown("""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 20px; border-radius: 16px; min-height: 220px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                    <div style="font-weight: 700; font-size: 1rem; color: #0f172a; margin-bottom: 16px;">Match Breakdown</div>
                """, unsafe_allow_html=True)
                
                breakdown_metrics = [
                    ("Skills", audit.get("hard_skills", {}).get("score", 90)),
                    ("Keywords", 85),
                    ("Experience", 88),
                    ("Impact & Metrics", audit.get("impact_metrics", {}).get("score", 75)),
                    ("Formatting", audit.get("formatting", {}).get("score", 80))
                ]
                for label, val in breakdown_metrics:
                    st.write(f"**{label}** — `{val}%`")
                    st.progress(val)
                st.markdown("</div>", unsafe_allow_html=True)

                # AI Suggestions Box
                st.markdown("""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 20px; border-radius: 16px; min-height: 200px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                    <div style="font-weight: 700; font-size: 1rem; color: #0f172a; margin-bottom: 12px;">AI Suggestions <span style="font-size: 0.7rem; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 6px;">Beta</span></div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5; margin-bottom: 8px;">- Add quantifiable percentages and metrics to experience bullets.</div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5; margin-bottom: 8px;">- Integrate missing technical skills directly into competencies.</div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">- Ensure layout geometry strictly aligns with A4 page constraints.</div>
                </div>
                """, unsafe_allow_html=True)

            # COMBINED JOB COMPATIBILITY & ALIGNMENT STRATEGY SECTION
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 24px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a; margin-bottom: 10px;">Job Compatibility & Alignment Strategy</div>
                <div style="font-size: 0.9rem; color: #334155; line-height: 1.6; margin-bottom: 14px;">
                    <strong>Role Fitness Summary:</strong> {fitness.get('role_fitness_summary', 'Strong analytical foundation with direct domain experience matching core technical requirements.')}
                </div>
                <div style="font-size: 0.9rem; color: #334155; line-height: 1.6; margin-bottom: 14px;">
                    <strong>Gaps & Missing Elements:</strong> {fitness.get('gaps_and_missing_elements', 'Minor gaps in secondary cloud pipelines and advanced dashboard configuration.')}
                </div>
                <div style="font-weight: 700; font-size: 0.95_rem; color: #0f172a; margin-bottom: 6px;">Strategic Alignment Roadmap:</div>
                <ul style="margin: 0; padding-left: 18px; font-size: 0.88rem; color: #475569; line-height: 1.6;">
            """, unsafe_allow_html=True)
            
            strat_points = fitness.get('alignment_strategy', [
                "Highlight automated ETL data processing pipelines and record scale to demonstrate senior execution capability.",
                "Position technical competencies upfront to capture immediate ATS keyword weighting.",
                "Ensure bullet points strictly adhere to the Google XYZ impact formula."
            ])
            for strat in strat_points:
                st.markdown(f"<li>{strat}</li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)

        else:
            # OPTIMIZED RESUME PREVIEW TAB
            st.markdown("""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 24px; border-radius: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                <div>
                    <div style="font-weight: 800; font-size: 1.2rem; color: #0f172a;">Optimized Resume Preview</div>
                    <div style="font-size: 0.88rem; color: #64748b; margin-top: 2px;">Fully tailored, executive-formatted A4 document ready for export.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            paper_html = generate_paper_sheet_tailored_html(res)
            components.html(paper_html, height=920, scrolling=True)

    st.markdown("<br>", unsafe_allow_html=True)
