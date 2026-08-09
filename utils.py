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

def generate_standard_resume_sheet_html(title_header, content_text_or_lines, is_docx_file=False):
    """Renders the Original Master Resume in the EXACT same executive A4 template as the optimized preview."""
    paragraphs_html = ""
    if is_docx_file and isinstance(content_text_or_lines, bytes):
        try:
            doc = docx.Document(BytesIO(content_text_or_lines))
            for p in doc.paragraphs:
                txt = html.escape(p.text.strip())
                if txt:
                    if txt.isupper() and len(txt) < 40:
                        paragraphs_html += f'<div style="color: #1e3a8a; font-size: 0.95rem; margin-top: 18px; margin-bottom: 8px; border-bottom: 1.5px solid #0f172a; padding-bottom: 4px; font-weight: 700; text-transform: uppercase; font-family: Segoe UI, sans-serif;">{txt}</div>'
                    else:
                        paragraphs_html += f'<p style="font-size: 0.88rem; line-height: 1.55; color: #334155; margin-bottom: 8px; font-family: Segoe UI, sans-serif;">{txt}</p>'
        except Exception:
            paragraphs_html = f'<p style="font-size:0.88rem;">{html.escape(str(content_text_or_lines))}</p>'
    else:
        lines = str(content_text_or_lines).split('\n')
        for line in lines:
            txt = html.escape(line.strip())
            if txt:
                if txt.isupper() and len(txt) < 40:
                    paragraphs_html += f'<div style="color: #1e3a8a; font-size: 0.95rem; margin-top: 18px; margin-bottom: 8px; border-bottom: 1.5px solid #0f172a; padding-bottom: 4px; font-weight: 700; text-transform: uppercase; font-family: Segoe UI, sans-serif;">{txt}</div>'
                else:
                    paragraphs_html += f'<p style="font-size: 0.88rem; line-height: 1.55; color: #334155; margin-bottom: 8px; font-family: Segoe UI, sans-serif;">{txt}</p>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #ffffff;
                color: #1e293b;
                margin: 0;
                padding: 30px;
            }}
        </style>
    </head>
    <body>
        {paragraphs_html}
    </body>
    </html>
    """

def generate_paper_sheet_tailored_html(results):
    """
    Renders an executive A4-styled HTML document with styled headers, 
    Google XYZ bullets, and yellow highlights + underlines on modified keywords.
    """
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    
    summary = html.escape(str(sec2.get("professional_summary", "")))
    skills_grouped = sec2.get("core_competencies_grouped", {})
    exp_list = sec2.get("professional_experience", [])
    proj_list = sec2.get("projects", [])

    # Apply inline yellow highlights AND underlines to keywords
    for kw in keywords:
        if len(kw) > 2 and kw in summary:
            escaped_kw = html.escape(kw)
            summary = summary.replace(
                escaped_kw, 
                f'<mark style="background-color: #fef08a; text-decoration: underline; padding: 2px 5px; border-radius: 4px; font-weight: 600; color: #1e293b;">{escaped_kw}</mark>'
            )

    skills_html = ""
    for cat, val in skills_grouped.items():
        skills_html += f'<div style="margin-bottom: 6px; font-size: 0.88rem;"><strong>{html.escape(str(cat))}:</strong> <span style="color: #0369a1;">{html.escape(str(val))}</span></div>'

    exp_html = ""
    for role in exp_list:
        role_title = html.escape(str(role.get("role_title", "")))
        exp_html += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.95rem; margin-top: 14px;">{role_title}</p><ul style="margin-top: 4px; margin-bottom: 12px; padding-left: 20px; font-size: 0.88rem; line-height: 1.6;">'
        for b in role.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            # Highlight added/rephrased metrics in bullets
            for kw in keywords:
                if len(kw) > 3 and kw in clean_b:
                    escaped_kw = html.escape(kw)
                    clean_b = clean_b.replace(escaped_kw, f'<mark style="background-color: #fef08a; text-decoration: underline; padding: 1px 4px; border-radius: 3px; font-weight: 600;">{escaped_kw}</mark>')
            exp_html += f'<li style="margin-bottom: 6px;">{clean_b}</li>'
        exp_html += '</ul>'

    proj_html = ""
    for proj in proj_list:
        proj_title = html.escape(str(proj.get("project_title", "")))
        proj_html += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.95rem; margin-top: 14px;">{proj_title}</p><ul style="margin-top: 4px; margin-bottom: 12px; padding-left: 20px; font-size: 0.88rem; line-height: 1.6;">'
        for b in proj.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            proj_html += f'<li style="margin-bottom: 6px;">{clean_b}</li>'
        proj_html += '</ul>'

    full_document_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #ffffff;
                color: #1e293b;
                margin: 0;
                padding: 30px;
            }}
            .section-title {{
                color: #1e3a8a;
                font-size: 0.98rem;
                margin-top: 18px;
                margin-bottom: 8px;
                border-bottom: 1.5px solid #0f172a;
                padding-bottom: 4px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="section-title">Professional Summary</div>
        <p style="font-size: 0.88rem; line-height: 1.6; color: #334155; margin-bottom: 18px;">{summary}</p>

        <div class="section-title">Technical Skills & Competencies</div>
        <div>{skills_html}</div>

        <div class="section-title">Professional Experience</div>
        <div>{exp_html}</div>

        <div class="section-title">Key Projects</div>
        <div>{proj_html}</div>
    </body>
    </html>
    """
    return full_document_html

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
    """Generates the downloadable .docx file WITHOUT web highlights or underlines."""
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
