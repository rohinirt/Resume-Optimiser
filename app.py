import docx
import base64
import html
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

def get_pdf_preview_html(pdf_bytes, height=800):
    """Generates an embedded iframe for full original PDF document viewing."""
    if not pdf_bytes:
        return "<p>No document bytes available for preview.</p>"
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}px" style="border:1px solid #cbd5e1; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.08);"></iframe>'

def get_docx_preview_html(uploaded_bytes_or_file, height=800):
    """Renders Word Document paragraphs into clean structured HTML."""
    try:
        if isinstance(uploaded_bytes_or_file, bytes):
            doc = docx.Document(BytesIO(uploaded_bytes_or_file))
        else:
            uploaded_bytes_or_file.seek(0)
            doc = docx.Document(uploaded_bytes_or_file)
            uploaded_bytes_or_file.seek(0)
        
        paragraphs_html = ""
        for p in doc.paragraphs:
            txt = html.escape(p.text.strip())
            if txt:
                # Basic header detection for visual formatting
                if txt.isupper() and len(txt) < 40:
                    paragraphs_html += f'<h4 style="color:#0f172a; margin-top:16px; margin-bottom:6px; border-bottom:1px solid #cbd5e1; padding-bottom:4px; font-family:sans-serif;">{txt}</h4>'
                else:
                    paragraphs_html += f'<p style="font-size:0.88rem; line-height:1.5; color:#334155; margin-bottom:8px; font-family:sans-serif;">{txt}</p>'
        
        return f'<div style="background-color:#ffffff; padding:25px; border-radius:8px; border:1px solid #cbd5e1; height:{height}px; overflow-y:auto; box-shadow:0 4px 12px rgba(0,0,0,0.05);">{paragraphs_html}</div>'
    except Exception as e:
        return f'<div style="padding:20px; color:red;">Unable to render DOCX preview: {str(e)}</div>'

def generate_paper_sheet_tailored_html(results):
    """
    Renders the optimized resume as an HTML document with yellow highlights 
    on matching keywords and bold metrics.
    """
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    
    summary = html.escape(sec2.get("professional_summary", ""))
    skills_grouped = sec2.get("core_competencies_grouped", {})
    exp_list = sec2.get("professional_experience", [])
    proj_list = sec2.get("projects", [])

    # Highlight keywords with yellow inline badges
    for kw in keywords:
        if len(kw) > 2 and kw in summary:
            escaped_kw = html.escape(kw)
            summary = summary.replace(escaped_kw, f'<mark style="background-color: #fef08a; padding: 2px 4px; border-radius: 3px; font-weight: 600; color: #1e293b;">{escaped_kw}</mark>')

    html_out = """
    <div style="background-color: #ffffff; padding: 35px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 8px 20px rgba(0,0,0,0.06); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; max-height: 800px; overflow-y: auto;">
        
        <div style="border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 20px;">
            <h3 style="margin: 0; font-size: 1.3rem; letter-spacing: 0.5px; color: #0f172a; font-weight: 700;">OPTIMIZED TAILORED RESUME</h3>
            <span style="font-size: 0.8rem; color: #64748b;">Yellow highlights indicate matched ATS keywords and Google XYZ bullet metrics</span>
        </div>

        <h4 style="color: #1e3a8a; font-size: 1rem; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; font-weight:700;">PROFESSIONAL SUMMARY</h4>
        <p style="font-size: 0.88rem; line-height: 1.6; color: #334155; margin-bottom: 20px;">""" + summary + """</p>
        
        <h4 style="color: #1e3a8a; font-size: 1rem; margin-top: 15px; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; font-weight:700;">TECHNICAL SKILLS & COMPETENCIES</h4>
        <div style="font-size: 0.88rem; line-height: 1.8; color: #334155; margin-bottom: 20px;">
    """
    
    for cat, val in skills_grouped.items():
        html_out += f'<div style="margin-bottom: 4px;"><strong>{html.escape(str(cat))}:</strong> <span style="color: #0369a1;">{html.escape(str(val))}</span></div>'
        
    html_out += """
        </div>
        <h4 style="color: #1e3a8a; font-size: 1rem; margin-top: 15px; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; font-weight:700;">PROFESSIONAL EXPERIENCE</h4>
    """

    for role in exp_list:
        role_title = html.escape(str(role.get("role_title", "")))
        html_out += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.92rem; margin-top:12px;">{role_title}</p><ul style="margin-top: 4px; margin-bottom: 12px; padding-left: 20px; font-size: 0.86rem; line-height: 1.55;">'
        for b in role.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            html_out += f'<li style="margin-bottom: 6px;">{clean_b}</li>'
        html_out += '</ul>'

    html_out += """
        <h4 style="color: #1e3a8a; font-size: 1rem; margin-top: 15px; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; font-weight:700;">KEY PROJECTS</h4>
    """

    for proj in proj_list:
        proj_title = html.escape(str(proj.get("project_title", "")))
        html_out += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.92rem; margin-top:12px;">{proj_title}</p><ul style="margin-top: 4px; margin-bottom: 12px; padding-left: 20px; font-size: 0.86rem; line-height: 1.55;">'
        for b in proj.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            html_out += f'<li style="margin-bottom: 6px;">{clean_b}</li>'
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
