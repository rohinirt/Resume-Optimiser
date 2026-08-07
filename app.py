import streamlit as st
from utils import extract_text_from_file, create_docx
from agent_engine import analyze_and_optimize_resume

st.set_page_config(page_title="AI Resume Tailor & ATS Optimizer", layout="wide")

st.title("🎯 AI ATS Resume Tailor")
st.caption("Upload your Master Resume & Job Description to auto-align and boost your ATS score.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input Data")
    uploaded_resume = st.file_uploader("Upload Master Resume (.pdf or .docx)", type=["pdf", "docx"])
    projects_input = st.text_area("Additional Projects / Work Experience Repository", height=150)
    jd_input = st.text_area("Paste Job Description (JD) Here", height=200)
    
    submit_btn = st.button("🚀 Analyze & Optimize Resume", type="primary")

if submit_btn and uploaded_resume and jd_input:
    with st.spinner("Agent is calculating ATS score and tailoring your resume..."):
        # Parse uploads
        resume_text = extract_text_from_file(uploaded_resume)
        
        # Call AI Agent
        results = analyze_and_optimize_resume(resume_text, projects_input, jd_input)
        
        # Store in session state for downloading
        st.session_state['results'] = results

with col2:
    st.subheader("2. Optimization Results")
    if 'results' in st.session_state:
        res = st.session_state['results']
        
        # Requirement 1 & 2: Score & Fitness Analysis
        m1, m2 = st.columns(2)
        m1.metric("Current ATS Score", f"{res['initial_ats_score']}%")
        m2.metric("Post-Alignment ATS Score", f"{res['updated_ats_score']}%", delta=f"+{res['updated_ats_score'] - res['initial_ats_score']}%")
        
        st.write("**Fitness to Role:**", res['fitness_summary'])
        st.success(f"**Matching Keywords:** {', '.join(res['matching_keywords'])}")
        st.error(f"**Missing Keywords:** {', '.join(res['missing_keywords'])}")
        
        st.markdown("---")
        
        # Requirement 3: Edited Resume Content
        st.subheader("3. Tailored Resume Preview")
        st.text_area("Optimized Content", res['suggested_rewrites'], height=250)
        
        st.markdown("---")
        
        # Requirement 5 & 6: Smart Filename & Download Actions
        filename = res['suggested_filename']
        docx_file = create_docx(res['suggested_rewrites'])
        
        st.write(f"**Suggested Target Name:** `{filename}.docx`")
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📥 Download Word (.docx)",
                data=docx_file,
                file_name=f"{filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
