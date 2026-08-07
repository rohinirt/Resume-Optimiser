
import streamlit as st
from utils import (
    extract_text_from_file, 
    get_pdf_preview_html, 
    get_docx_preview_text, 
    build_updated_docx
)
from agent_engine import analyze_and_optimize_resume

st.set_page_config(page_title="ATS Resume Optimization Agent", layout="wide")

st.title("🎯 AI ATS Resume Tailor & Optimization Agent")
st.caption("Tailor your Master Resume against Job Descriptions while preserving document structure and tracking ATS scores.")

# ==========================================
# ROW 1: INPUT DATA SECTIONS
# ==========================================
st.markdown("### 📥 Row 1: Input Data")

col_in1, col_in2, col_in3 = st.columns([1, 1, 1])

with col_in1:
    uploaded_file = st.file_uploader(
        "Upload Master Resume (.pdf or .docx)", 
        type=["pdf", "docx"],
        key="master_resume_uploader"
    )

with col_in2:
    projects_input = st.text_area(
        "Work Projects & Experience Repository", 
        height=180,
        placeholder="Paste details of additional projects, raw metrics, repository links, or past roles..."
    )

with col_in3:
    jd_input = st.text_area(
        "Job Description (JD)", 
        height=180,
        placeholder="Paste full Job Description here..."
    )

analyze_btn = st.button("🚀 Analyze & Optimize Resume", type="primary", use_container_width=True)

if analyze_btn:
    if not uploaded_file or not jd_input:
        st.warning("Please upload a Master Resume and paste a Job Description to proceed.")
    else:
        with st.spinner("AI Agent is analyzing JD keywords, scoring, and preparing section rewrites..."):
            try:
                resume_bytes = uploaded_file.read()
                uploaded_file.seek(0)
                st.session_state['resume_bytes'] = resume_bytes
                st.session_state['file_name'] = uploaded_file.name
                st.session_state['file_type'] = uploaded_file.name.split(".")[-1].lower()

                resume_text = extract_text_from_file(uploaded_file)
                results = analyze_and_optimize_resume(resume_text, projects_input, jd_input)
                st.session_state['results'] = results
                st.success("Optimization Complete!")
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")

st.markdown("---")

# ==========================================
# ROW 2: PREVIEW & OPTIMIZATION RESULTS
# ==========================================
st.markdown("### 📊 Row 2: Resume Preview & Tailored Suggestions")

col_left, col_right = st.columns([1, 1])

# LEFT COLUMN: PREVIEW OF UPLOADED RESUME
with col_left:
    st.subheader("👁️ Uploaded Resume Preview")
    if 'resume_bytes' in st.session_state and st.session_state['resume_bytes']:
        file_type = st.session_state.get('file_type', '')
        if file_type == 'pdf':
            pdf_html = get_pdf_preview_html(st.session_state['resume_bytes'])
            st.markdown(pdf_html, unsafe_allow_html=True)
        elif file_type == 'docx':
            docx_text = get_docx_preview_text(uploaded_file) if uploaded_file else ""
            st.text_area("DOCX Document Preview", docx_text, height=580, disabled=True)
    else:
        st.info("Upload a document in Row 1 to view the preview here.")

# RIGHT COLUMN: OPTIMIZATION RESULTS & SECTION SELECTION
with col_right:
    st.subheader("⚡ Optimization Results & Section Controls")
    
    if 'results' in st.session_state:
        res = st.session_state['results']
        sec1 = res.get("section_1_analysis", {})
        sec2 = res.get("section_2_tailored_content", {})
        sec3 = res.get("section_3_results", {})

        # ATS SCORES
        score_col1, score_col2 = st.columns(2)
        initial_score = sec1.get("initial_ats_score", 0)
        updated_score = sec3.get("updated_ats_score", 0)
        
        score_col1.metric("Pre-ATS Score", f"{initial_score}/100")
        score_col2.metric("Post-ATS Score", f"{updated_score}/100", delta=f"+{updated_score - initial_score}%")

        # Clarifying Questions if AI has doubt
        questions = sec3.get("clarifying_questions", [])
        if questions and len(questions) > 0 and questions[0]:
            st.warning("❓ **Clarifying Questions from Agent:**\n" + "\n".join([f"- {q}" for q in questions if q]))

        # SECTION 1 ANALYSIS EXPANDER
        with st.expander("🔍 **JD Analysis & Strategy**", expanded=False):
            st.write("**Top JD Keywords:**", ", ".join(sec1.get("top_jd_keywords", [])))
            st.write("**Gaps Assessment:**", sec1.get("resume_match_and_gaps", ""))
            st.write("**Strategy:**")
            for strat in sec1.get("tailoring_strategy", []):
                st.write(f"- {strat}")

        st.markdown("#### Select Sections to Apply:")
        
        # 1. Professional Summary Toggle
        apply_summary = st.checkbox("Apply Professional Summary", value=True, key="chk_summary")
        summary_data = sec2.get("professional_summary", {})
        st.info(f"**Suggested Summary:**\n{summary_data.get('suggested_text', '')}")
        st.caption(f"*Justification:* {summary_data.get('justification', '')}")

        st.markdown("---")

        # 2. Core Competencies / Skills Toggle
        apply_skills = st.checkbox("Apply Core Competencies / Skills", value=True, key="chk_skills")
        skills_data = sec2.get("core_competencies", {})
        st.write("**Suggested Skills:**", ", ".join(skills_data.get("suggested_skills", [])))
        if skills_data.get("missing_skills"):
            st.error(f"**Missing Skills in Resume:** {', '.join(skills_data.get('missing_skills', []))}")
        st.caption(f"*Justification:* {skills_data.get('justification', '')}")

        st.markdown("---")

        # 3. Professional Experience Toggle
        apply_exp = st.checkbox("Apply Professional Experience", value=True, key="chk_exp")
        exp_data = sec2.get("professional_experience", [])
        for role in exp_data:
            st.write(f"**{role.get('role_title', 'Role')}**")
            for b in role.get("suggested_bullets", []):
                st.write(f"- {b}")
            st.caption(f"*Justification:* {role.get('justification', '')}")

        st.markdown("---")

        # 4. Projects Toggle
        apply_projects = st.checkbox("Apply Selected Projects", value=True, key="chk_projects")
        projects_data = sec2.get("projects", {})
        for proj in projects_data.get("selected_projects", []):
            st.write(f"**{proj.get('project_title', 'Project')}**")
            for b in proj.get("suggested_bullets", []):
                st.write(f"- {b}")
            st.caption(f"*Reasoning:* {proj.get('selection_reasoning', '')}")

        st.markdown("---")
        
        # Salary Benchmark Info
        if sec3.get("estimated_salary_info"):
            st.success(f"💰 **Estimated Role Salary Benchmark:** {sec3.get('estimated_salary_info')}")

        # GENERATE & DOWNLOAD BUTTON
        st.markdown("### 💾 Export Document")
        suggested_filename = sec3.get("suggested_filename", "Tailored_Resume") + ".docx"
        
        selections = {
            "apply_summary": apply_summary,
            "apply_skills": apply_skills,
            "apply_exp": apply_exp,
            "apply_projects": apply_projects
        }

        updated_docx_io = build_updated_docx(
            st.session_state.get('resume_bytes', b""),
            res,
            selections
        )

        st.download_button(
            label="📥 Download Updated Resume (.docx)",
            data=updated_docx_io,
            file_name=suggested_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
    else:
        st.info("Fill inputs in Row 1 and click 'Analyze & Optimize Resume' to see recommendations.")
