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

def get_pdf_preview_html(pdf_bytes, height=850):
    """Generates an embedded iframe for full original PDF viewing."""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}" style="border:1px solid #cbd5e1; border-radius:8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);"></iframe>'

def get_docx_preview_text(uploaded_file_or_bytes):
    """Reads docx paragraphs into clean formatted text for display."""
    if isinstance(uploaded_file_or_bytes, bytes):
        if not uploaded_file_or_bytes:
            return ""
        doc = docx.Document(BytesIO(uploaded_file_or_bytes))
    else:
        uploaded_file_or_bytes.seek(0)
        doc = docx.Document(uploaded_file_or_bytes)
        uploaded_file_or_bytes.seek(0)
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(lines)

def generate_paper_sheet_tailored_html(results):
    """
    Renders an optimized resume as a realistic A4 white paper sheet document 
    with highlighted keywords and formatted bullet points.
    """
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    
    summary = sec2.get("professional_summary", "")
    skills_grouped = sec2.get("core_competencies_grouped", {})
    exp_list = sec2.get("professional_experience", [])
    proj_list = sec2.get("projects", [])

    # Apply inline yellow highlights to keywords
    for kw in keywords:
        if len(kw) > 2 and kw in summary:
            summary = summary.replace(kw, f'<mark style="background-color: #fef08a; padding: 2px 4px; border-radius: 3px; font-weight: 600; color: #1e293b;">{kw}</mark>')

    html_out = f"""
    <div style="background-color: #ffffff; padding: 40px; border-radius: 4px; border: 1px solid #cbd5e1; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); font-family: 'Times New Roman', Times, serif, sans-serif; color: #1e293b; max-height: 850px; overflow-y: auto;">
        
        <!-- HEADER / TITLE -->
        <div style="border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 20px;">
            <h2 style="margin: 0; font-size: 1.4rem; letter-spacing: 0.5px; color: #0f172a; font-family: sans-serif; font-weight: 700;">OPTIMIZED RESUME PREVIEW</h2>
            <span style="font-size: 0.8rem; color: #64748b; font-family: sans-serif;">Yellow highlights indicate aligned ATS keywords & optimized bullet metrics</span>
        </div>

        <!-- PROFESSIONAL SUMMARY -->
        <h3 style="color: #1e3a8a; font-size: 1.05rem; margin-bottom: 6px; font-family: sans-serif; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">PROFESSIONAL SUMMARY</h3>
        <p style="font-size: 0.9rem; line-height: 1.6; color: #334155; margin-bottom: 20px;">{summary}</p>
        
        <!-- CORE COMPETENCIES -->
        <h3 style="color: #1e3a8a; font-size: 1.05rem; margin-top: 15px; margin-bottom: 6px; font-family: sans-serif; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">TECHNICAL SKILLS & COMPETENCIES</h3>
        <div style="font-size: 0.88rem; line-height: 1.8; color: #334155; margin-bottom: 20px;">
    """
    
    for cat, val in skills_grouped.items():
        html_out += f'<div style="margin-bottom: 4px;"><strong>{cat}:</strong> <span style="color: #0369a1;">{val}</span></div>'
        
    html_out += """
        </div>

        <!-- PROFESSIONAL EXPERIENCE -->
        <h3 style="color: #1e3a8a; font-size: 1.05rem; margin-top: 15px; margin-bottom: 6px; font-family: sans-serif; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">PROFESSIONAL EXPERIENCE</h3>
    """

    for role in exp_list:
        html_out += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.95rem;">{role.get("role_title")}</p><ul style="margin-top: 4px; margin-bottom: 16px; padding-left: 20px; font-size: 0.88rem; line-height: 1.55;">'
        for b in role.get("bullets", []):
            html_out += f'<li style="margin-bottom: 6px;">{b}</li>'
        html_out += '</ul>'

    html_out += """
        <!-- PROJECTS -->
        <h3 style="color: #1e3a8a; font-size: 1.05rem; margin-top: 15px; margin-bottom: 6px; font-family: sans-serif; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">KEY PROJECTS</h3>
    """

    for proj in proj_list:
        html_out += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.95rem;">{proj.get("project_title")}</p><ul style="margin-top: 4px; margin-bottom: 16px; padding-left: 20px; font-size: 0.88rem; line-height: 1.55;">'
        for b in proj.get("bullets", []):
            html_out += f'<li style="margin-bottom: 6px;">{b}</li>'
        html_out += '</ul>'

    html_out += "</div>"
    return html_out

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
    output = BytesIO()
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

    if is_docx:
        p_texts = [p.text.strip().upper() for p in doc.paragraphs]

        if selections.get("apply_summary", True) and "PROFESSIONAL SUMMARY" in p_texts:
            idx = p_texts.index("PROFESSIONAL SUMMARY")
            if idx + 1 < len(doc.paragraphs):
                replace_paragraph_text_keep_formatting(doc.paragraphs[idx + 1], sec2.get("professional_summary", ""))

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

    else:
        doc.add_heading("TAILORED RESUME", level=1)

        if selections.get("apply_summary", True):
            doc.add_heading("PROFESSIONAL SUMMARY", level=2)
            doc.add_paragraph(sec2.get("professional_summary", ""))

        if selections.get("apply_skills", True):
            doc.add_heading("TECHNICAL SKILLS", level=2)
            grouped_skills = sec2.get("core_competencies_grouped", {})
            for cat, val in grouped_skills.items():
                p = doc.add_paragraph()
                r = p.add_run(f"{cat}: ")
                r.bold = True
                p.add_run(str(val))

        if selections.get("apply_exp", True):
            doc.add_heading("WORK EXPERIENCE", level=2)
            for role in sec2.get("professional_experience", []):
                doc.add_heading(role.get("role_title", "Role"), level=3)
                for b in role.get("bullets", []):
                    p = doc.add_paragraph(b)
                    p.paragraph_format.left_indent = docx.shared.Inches(0.25)

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
