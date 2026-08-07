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
st.caption("Auto-align Master Resumes to JDs with in-place Word document editing.")

# ROW 1: INPUT DATA
st.markdown("### 📥 Input Data")
col1, col2, col3 = st.columns(3)

with col1:
    uploaded_file = st.file_uploader("Upload Master Resume (.pdf or .docx)", type=["pdf", "docx"])
with col2:
    projects_input = st.text_area("Additional Projects / Work Experience", height=150)
with col3:
    jd_input = st.text_area("Paste Job Description (JD)", height=150)

analyze_btn = st.button("🚀 Analyze & Optimize Resume", type="primary", use_container_width=True)

if analyze_btn and uploaded_file and jd_input:
    with st.spinner("Analyzing resume and preparing in-place updates..."):
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        st.session_state['resume_bytes'] = file_bytes
        st.session_state['file_type'] = uploaded_file.name.split(".")[-1].lower()
        
        resume_text = extract_text_from_file(uploaded_file)
        results = analyze_and_optimize_resume(resume_text, projects_input, jd_input)
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
            text_preview = get_docx_preview_text(uploaded_file) if uploaded_file else ""
            st.text_area("Document View", text_preview, height=650, disabled=True)

    # RIGHT COLUMN: METRICS, FITNESS & SECTION CONTROLS
    with col_right:
        st.subheader("⚡ Pre vs. Post Optimization Metrics")

        m1, m2 = st.columns(2)
        m1.metric("Pre-ATS Score", f"{pre.get('ats_score', 0)}%")
        m2.metric("Post-ATS Score", f"{post.get('ats_score', 0)}%", delta=f"+{post.get('ats_score', 0) - pre.get('ats_score', 0)}%")

        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.markdown("##### 🔴 Pre-Optimization")
            st.success(f"**Matching:** {', '.join(pre.get('matching_keywords', []))}")
            st.error(f"**Missing:** {', '.join(pre.get('missing_keywords', []))}")

        with k_col2:
            st.markdown("##### 🟢 Post-Optimization")
            st.success(f"**Matching:** {', '.join(post.get('matching_keywords', []))}")
            st.error(f"**Missing:** {', '.join(post.get('missing_keywords', []))}")

        st.markdown("---")

        # RESTORED: ROLE FITNESS, GAPS & ALIGNMENT STRATEGY
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

        apply_skills = st.checkbox("Apply Core Competencies / Skills", value=True)
        st.write(", ".join(sec2.get("core_competencies", [])))

        apply_exp = st.checkbox("Apply Professional Experience Bullets", value=True)
        for role in sec2.get("professional_experience", []):
            st.caption(f"**{role.get('role_title')}**")
            for b in role.get("bullets", []):
                st.write(f"- {b}")

        apply_projects = st.checkbox("Apply Projects Bullets", value=True)
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
            res,
            selections
        )

        filename = res.get("suggested_filename", "Rohini_Tembhurnikar_Resume") + ".docx"

        st.download_button(
            label="📥 Download Updated Resume (.docx)",
            data=updated_docx,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
