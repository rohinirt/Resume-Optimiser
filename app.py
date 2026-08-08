import streamlit as st
from utils import (
    extract_text_from_file, 
    get_pdf_preview_html, 
    get_docx_preview_text, 
    build_updated_docx_inplace
)
from agent_engine import analyze_and_optimize_resume

st.set_page_config(page_title="ATS Resume Tailor", layout="wide")

st.title("🎯 AI ATS Resume Tailor")
st.caption("Upload Master Resume, Experience, and Project files to auto-align against Job Descriptions.")

# ROW 1: INPUT DATA SECTIONS WITH DEDICATED FILE UPLOADERS
st.markdown("### 📥 Input Files & Job Description")
col1, col2, col3, col4 = st.columns(4)

with col1:
    uploaded_resume = st.file_uploader("1. Master Resume (.pdf / .docx)", type=["pdf", "docx"], key="upload_resume")

with col2:
    uploaded_experience = st.file_uploader("2. Work Experience File (.pdf / .docx)", type=["pdf", "docx"], key="upload_exp")

with col3:
    uploaded_projects = st.file_uploader("3. Projects Repository File (.pdf / .docx)", type=["pdf", "docx"], key="upload_proj")

with col4:
    jd_input = st.text_area("4. Paste Job Description (JD)", height=140, placeholder="Paste JD requirements here...")

analyze_btn = st.button("🚀 Analyze & Optimize Resume", type="primary", use_container_width=True)

if analyze_btn and uploaded_resume and jd_input:
    with st.spinner("Extracting content from files, running deep ATS keyword matching, and tailoring resume..."):
        file_bytes = uploaded_resume.read()
        uploaded_resume.seek(0)
        st.session_state['resume_bytes'] = file_bytes
        st.session_state['file_type'] = uploaded_resume.name.split(".")[-1].lower()
        
        # Parse text from all uploaded files
        resume_text = extract_text_from_file(uploaded_resume)
        experience_text = extract_text_from_file(uploaded_experience) if uploaded_experience else ""
        projects_text = extract_text_from_file(uploaded_projects) if uploaded_projects else ""
        
        results = analyze_and_optimize_resume(resume_text, projects_text, experience_text, jd_input)
        st.session_state['results'] = results

st.markdown("---")

# ROW 2: PREVIEW & RESULTS
if 'results' in st.session_state:
    res = st.session_state['results']
    pre = res.get("pre_optimization", {})
    post = res.get("post_optimization", {})
    fitness = res.get("fitness_and_strategy", {})
    sec2 = res.get("section_2_tailored_content", {})

    col_left, col_right = st.columns([1, 1])

    # LEFT COLUMN: ORIGINAL RESUME PREVIEW
    with col_left:
        st.subheader("👁️ Master Resume Preview")
        if st.session_state.get('file_type') == 'pdf':
            st.markdown(get_pdf_preview_html(st.session_state['resume_bytes']), unsafe_allow_html=True)
        else:
            text_preview = get_docx_preview_text(uploaded_resume) if uploaded_resume else ""
            st.text_area("Document View", text_preview, height=650, disabled=True)

    # RIGHT COLUMN: METRICS, FITNESS & SECTION CONTROLS
    with col_right:
        st.subheader("⚡ ATS Scores & Detailed Keyword Match")

        m1, m2 = st.columns(2)
        m1.metric("Pre-ATS Score", f"{pre.get('ats_score', 0)}%")
        m2.metric("Post-ATS Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")

        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.markdown("##### 🔴 Pre-Optimization Keywords")
            st.success(f"**Matching:** {', '.join(pre.get('matching_keywords', []))}")
            st.error(f"**Missing:** {', '.join(pre.get('missing_keywords', []))}")

        with k_col2:
            st.markdown("##### 🟢 Post-Optimization Keywords")
            st.success(f"**Matching:** {', '.join(post.get('matching_keywords', []))}")
            st.error(f"**Missing:** {', '.join(post.get('missing_keywords', []))}")

        st.markdown("---")

        # ROLE FITNESS & ALIGNMENT STRATEGY
        with st.expander("📌 **Role Fitness, Gaps & Alignment Strategy**", expanded=True):
            st.write("**Fitness Summary:**", fitness.get("role_fitness_summary", ""))
            st.write("**Missing Elements & Gaps:**", fitness.get("gaps_and_missing_elements", ""))
            st.write("**Alignment Positioning Strategy:**")
            for strat in fitness.get("alignment_strategy", []):
                st.write(f"- {strat}")

        st.markdown("---")
        st.subheader("🛠️ Mark Sections to Apply")

        apply_summary = st.checkbox("Apply Professional Summary", value=True)
        st.info(sec2.get("professional_summary", ""))

        apply_skills = st.checkbox("Apply Grouped Core Competencies / Skills", value=True)
        skills_grouped = sec2.get("core_competencies_grouped", {})
        for category, skills in skills_grouped.items():
            st.write(f"**{category}:** {skills}")

        apply_exp = st.checkbox("Apply Professional Experience Bullets", value=True)
        for role in sec2.get("professional_experience", []):
            st.caption(f"**{role.get('role_title')}**")
            for b in role.get("bullets", []):
                st.write(f"- {b}")

        apply_projects = st.checkbox("Apply Selected Projects Bullets", value=True)
        for proj in sec2.get("projects", []):
            st.caption(f"**{proj.get('project_title')}**")
            for b in proj.get("bullets", []):
                st.write(f"- {b}")

        if res.get("salary_benchmark"):
            st.info(f"💰 **Salary Benchmark:** {res.get('salary_benchmark')}")

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
            label="📥 Download Updated Resume (.docx)",
            data=updated_docx,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
