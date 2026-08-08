import docx
import base64
from io import BytesIO
from pypdf import PdfReader

def extract_text_from_file(uploaded_file):
    if not uploaded_file:
        return ""
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
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" style="border:1px solid #ccc; border-radius:8px;"></iframe>'

def get_docx_preview_text(uploaded_file):
    uploaded_file.seek(0)
    doc = docx.Document(uploaded_file)
    uploaded_file.seek(0)
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(lines)

def replace_paragraph_text_keep_formatting(paragraph, new_text):
    if len(paragraph.runs) > 0:
        first_run = paragraph.runs[0]
        font_name = first_run.font.name
        font_size = first_run.font.size
        bold = first_run.bold
        italic = first_run.italic
        
        p_elem = paragraph._p
        for child in list(p_elem):
            if child.tag.endswith('r'):
                p_elem.remove(child)
                
        new_run = paragraph.add_run(new_text)
        new_run.font.name = font_name
        new_run.font.size = font_size
        new_run.bold = bold
        new_run.italic = italic
    else:
        paragraph.text = new_text

def build_updated_docx_inplace(original_file_bytes, file_type, results, selections):
    """
    Safely creates/edits a Word document.
    - If input was .docx: Performs in-place paragraph edits to retain original document formatting.
    - If input was .pdf: Creates a clean new .docx document populated with the AI tailored output.
    """
    output = BytesIO()
    
    # Check if the uploaded file is a true .docx file
    is_docx = (file_type == 'docx') and original_file_bytes and len(original_file_bytes) > 0

    if is_docx:
        try:
            doc = docx.Document(BytesIO(original_file_bytes))
        except Exception:
            doc = docx.Document()
            is_docx = False
    else:
        doc = docx.Document()

    sec2 = results.get("section_2_tailored_content", {})

    # BRANCH 1: IN-PLACE PARAGRAPH OVERWRITE FOR .DOCX FILES
    if is_docx:
        p_texts = [p.text.strip().upper() for p in doc.paragraphs]

        # 1. SUMMARY
        if selections.get("apply_summary", True) and "PROFESSIONAL SUMMARY" in p_texts:
            idx = p_texts.index("PROFESSIONAL SUMMARY")
            if idx + 1 < len(doc.paragraphs):
                replace_paragraph_text_keep_formatting(doc.paragraphs[idx + 1], sec2.get("professional_summary", ""))

        # 2. GROUPED SKILLS
        if selections.get("apply_skills", True):
            for header in ["TECHNICAL SKILLS", "CORE COMPETENCIES", "SKILLS"]:
                if header in p_texts:
                    idx = p_texts.index(header)
                    grouped_skills = sec2.get("core_competencies_grouped", {})
                    offset = 1
                    for cat, val in grouped_skills.items():
                        if idx + offset < len(doc.paragraphs):
                            text_line = f"{cat}: {val}"
                            replace_paragraph_text_keep_formatting(doc.paragraphs[idx + offset], text_line)
                            offset += 1
                    break

        # 3. EXPERIENCE BULLETS
        if selections.get("apply_exp", True) and "WORK EXPERIENCE" in p_texts:
            exp_idx = p_texts.index("WORK EXPERIENCE")
            exp_data = sec2.get("professional_experience", [])
            all_bullets = [b for role in exp_data for b in role.get("bullets", [])]
            
            bullet_counter = 0
            for i in range(exp_idx + 1, len(doc.paragraphs)):
                text = doc.paragraphs[i].text.strip()
                if text.upper() in ["PROJECTS", "EDUCATION", "CERTIFICATIONS"]:
                    break
                if len(text) > 15 and not any(k in text for k in ["Uber", "TopN Analytics", "Jan 202", "Oct 202"]):
                    if bullet_counter < len(all_bullets):
                        replace_paragraph_text_keep_formatting(doc.paragraphs[i], all_bullets[bullet_counter])
                        bullet_counter += 1

        # 4. PROJECTS
        if selections.get("apply_projects", True) and "PROJECTS" in p_texts:
            proj_idx = p_texts.index("PROJECTS")
            proj_data = sec2.get("projects", [])
            all_proj_bullets = [b for proj in proj_data for b in proj.get("bullets", [])]

            proj_counter = 0
            for i in range(proj_idx + 1, len(doc.paragraphs)):
                text = doc.paragraphs[i].text.strip()
                if text.upper() in ["EDUCATION", "CERTIFICATIONS"]:
                    break
                if len(text) > 15 and not any(k in text for k in ["Dashboard", "Optimization", "Tableau", "Python"]):
                    if proj_counter < len(all_proj_bullets):
                        replace_paragraph_text_keep_formatting(doc.paragraphs[i], all_proj_bullets[proj_counter])
                        proj_counter += 1

    # BRANCH 2: CLEAN NEW .DOCX GENERATION FOR PDF UPLOADS
    else:
        doc.add_heading("TAILORED RESUME", level=1)

        # 1. SUMMARY
        if selections.get("apply_summary", True):
            doc.add_heading("PROFESSIONAL SUMMARY", level=2)
            doc.add_paragraph(sec2.get("professional_summary", ""))

        # 2. GROUPED SKILLS
        if selections.get("apply_skills", True):
            doc.add_heading("TECHNICAL SKILLS", level=2)
            grouped_skills = sec2.get("core_competencies_grouped", {})
            for cat, val in grouped_skills.items():
                p = doc.add_paragraph()
                r = p.add_run(f"{cat}: ")
                r.bold = True
                p.add_run(str(val))

        # 3. EXPERIENCE BULLETS
        if selections.get("apply_exp", True):
            doc.add_heading("WORK EXPERIENCE", level=2)
            for role in sec2.get("professional_experience", []):
                doc.add_heading(role.get("role_title", "Role"), level=3)
                for b in role.get("bullets", []):
                    p = doc.add_paragraph(b)
                    p.paragraph_format.left_indent = docx.shared.Inches(0.25)

        # 4. PROJECTS
        if selections.get("apply_projects", True):
            doc.add_heading("PROJECTS", level=2)
            for proj in sec2.get("projects", []):
                doc.add_heading(proj.get("project_title", "Project"), level=3)
                for b in proj.get("bullets", []):
                    p = doc.add_paragraph(b)
                    p.paragraph_format.left_indent = docx.shared.Inches(0.25)

    doc.save(output)
    output.seek(0)
    return output
