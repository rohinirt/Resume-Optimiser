```python:utils.py
import docx
import base64
from io import BytesIO
from pypdf import PdfReader

def extract_text_from_file(uploaded_file):
    """Extracts raw text content from uploaded PDF or Word document."""
    text = ""
    uploaded_file.seek(0)
    if uploaded_file.name.endswith(".pdf"):
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    uploaded_file.seek(0)
    return text

def get_pdf_preview_html(pdf_bytes):
    """Generates an embedded iframe HTML string for PDF preview."""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border:1px solid #ccc; border-radius:8px;"></iframe>'
    return pdf_display

def get_docx_preview_text(uploaded_file):
    """Reads docx paragraphs into clean formatted text for display."""
    uploaded_file.seek(0)
    doc = docx.Document(uploaded_file)
    uploaded_file.seek(0)
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(lines)

def build_updated_docx(original_file_bytes, results, selections):
    """
    Creates an updated Word document by modifying or generating content
    while preserving document structure and font formatting where possible.
    """
    output = BytesIO()
    
    if original_file_bytes and len(original_file_bytes) > 0:
        doc = docx.Document(BytesIO(original_file_bytes))
    else:
        doc = docx.Document()

    # If the document has existing content, we append tailored sections
    # or replace matching sections cleanly.
    doc.add_heading("ATS Optimized Resume Suggestions", level=1)
    
    sec2 = results.get("section_2_tailored_content", {})

    # 1. Professional Summary
    if selections.get("apply_summary", True):
        doc.add_heading("Professional Summary", level=2)
        summary = sec2.get("professional_summary", {}).get("suggested_text", "")
        p = doc.add_paragraph(summary)
        p.style = doc.styles['Normal']

    # 2. Core Competencies / Skills
    if selections.get("apply_skills", True):
        doc.add_heading("Core Competencies & Skills", level=2)
        skills = sec2.get("core_competencies", {}).get("suggested_skills", [])
        if skills:
            doc.add_paragraph(", ".join(skills))

    # 3. Professional Experience
    if selections.get("apply_exp", True):
        doc.add_heading("Professional Experience", level=2)
        roles = sec2.get("professional_experience", [])
        for role in roles:
            doc.add_heading(role.get("role_title", "Role"), level=3)
            for bullet in role.get("suggested_bullets", []):
                p = doc.add_paragraph(bullet, style='List Bullet')

    # 4. Projects
    if selections.get("apply_projects", True):
        doc.add_heading("Key Analytics Projects", level=2)
        projects = sec2.get("projects", {}).get("selected_projects", [])
        for proj in projects:
            doc.add_heading(proj.get("project_title", "Project"), level=3)
            for bullet in proj.get("suggested_bullets", []):
                doc.add_paragraph(bullet, style='List Bullet')

    doc.save(output)
    output.seek(0)
    return output
