import docx
import base64
import html
import re
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

def get_pdf_preview_html(pdf_bytes, height=1150):
    """Embeds PDF binary cleanly with full page height to prevent internal scrollbars."""
    if not pdf_bytes:
        return "<p>No document available for preview.</p>"
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return f'<iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="{height}px" style="border:1px solid #cbd5e1; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.08); overflow:hidden;"></iframe>'

def get_docx_preview_html(uploaded_bytes_or_file, height=1150):
    """
    Renders Word Document using embedded JS parser to preserve 
    exact original fonts, borders, line spacing, and run bolding.
    """
    try:
        if isinstance(uploaded_bytes_or_file, bytes):
            docx_bytes = uploaded_bytes_or_file
        else:
            uploaded_bytes_or_file.seek(0)
            docx_bytes = uploaded_bytes_or_file.read()
            uploaded_bytes_or_file.seek(0)
        
        base64_docx = base64.b64encode(docx_bytes).decode('utf-8')
        
        # Mammoth JS Renderer embedded inside container for pixel-perfect Word formatting
        html_container = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #ffffff;
                    color: #0f172a;
                    padding: 35px;
                    margin: 0;
                    min-height: {height}px;
                }}
                p {{
                    margin-bottom: 6px;
                    line-height: 1.5;
                    font-size: 0.88rem;
                }}
                h1, h2, h3, h4 {{
                    color: #0f172a;
                    border-bottom: 1px solid #0f172a;
                    padding-bottom: 3px;
                    margin-top: 16px;
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    font-size: 0.95rem;
                }}
            </style>
        </head>
        <body>
            <div id="document-render">Loading Original Document Formatting...</div>
            <script>
                const base64Data = "{base64_docx}";
                const byteCharacters = atob(base64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {{
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }}
                const byteArray = new Uint8Array(byteNumbers);
                
                mammoth.convertToHtml({{arrayBuffer: byteArray.buffer}})
                    .then(function(result){{
                        document.getElementById('document-render').innerHTML = result.value;
                    }})
                    .catch(function(err){{
                        document.getElementById('document-render').innerHTML = "Error rendering Word doc.";
                    }});
            </script>
        </body>
        </html>
        """
        return html_container
    except Exception as e:
        return f'<div style="padding:20px; color:red;">Unable to render DOCX preview: {str(e)}</div>'

def generate_paper_sheet_tailored_html(results):
    """
    Renders optimized resume as a clean A4 sheet without unnecessary banners,
    using yellow highlights for keywords, green for metrics, and blue for bullet improvements.
    """
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    
    summary = html.escape(str(sec2.get("professional_summary", "")))
    skills_grouped = sec2.get("core_competencies_grouped", {})
    exp_list = sec2.get("professional_experience", [])
    proj_list = sec2.get("projects", [])

    # Highlight Keywords in Yellow
    for kw in keywords:
        if len(kw) > 2 and kw in summary:
            escaped_kw = html.escape(kw)
            summary = summary.replace(escaped_kw, f'<mark style="background-color: #fef08a; padding: 2px 5px; border-radius: 4px; font-weight: 600; color: #1e293b;">{escaped_kw}</mark>')

    # Highlight Metrics (%) in Green
    summary = re.sub(r'(\b\d+%\b|\b\d+K–\d+K\+\b|\b\d+\+\b)', r'<mark style="background-color: #bbf7d0; padding: 2px 5px; border-radius: 4px; font-weight: 600; color: #166534;">\1</mark>', summary)

    skills_html = ""
    for cat, val in skills_grouped.items():
        skills_html += f'<div style="margin-bottom: 6px; font-size: 0.88rem;"><strong>{html.escape(str(cat))}:</strong> <span style="color: #0369a1;">{html.escape(str(val))}</span></div>'

    exp_html = ""
    for role in exp_list:
        role_title = html.escape(str(role.get("role_title", "")))
        exp_html += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.95rem; margin-top: 14px;">{role_title}</p><ul style="margin-top: 4px; margin-bottom: 12px; padding-left: 20px; font-size: 0.88rem; line-height: 1.6;">'
        for b in role.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            # Highlight percentages/metrics in green
            clean_b = re.sub(r'(\b\d+%\b|\b\d+K–\d+K\+\b|\b\d+\+\b|\b\d+,\d+\+\b)', r'<mark style="background-color: #bbf7d0; padding: 2px 4px; border-radius: 3px; font-weight: 600; color: #166534;">\1</mark>', clean_b)
            exp_html += f'<li style="margin-bottom: 6px;">{clean_b}</li>'
        exp_html += '</ul>'

    proj_html = ""
    for proj in proj_list:
        proj_title = html.escape(str(proj.get("project_title", "")))
        proj_html += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 4px; font-size: 0.95rem; margin-top: 14px;">{proj_title}</p><ul style="margin-top: 4px; margin-bottom: 12px; padding-left: 20px; font-size: 0.88rem; line-height: 1.6;">'
        for b in proj.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            clean_b = re.sub(r'(\b\d+%\b|\b\d+,\d+\+\b|\b\d+\+\b)', r'<mark style="background-color: #bbf7d0; padding: 2px 4px; border-radius: 3px; font-weight: 600; color: #166534;">\1</mark>', clean_b)
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
                margin: 0 auto;
                padding: 40px;
                max-width: 800px;
                min-height: 1100px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
            }}
            .section-title {{
                color: #0f172a;
                font-size: 0.95rem;
                margin-top: 18px;
                margin-bottom: 8px;
                border-bottom: 1.5px solid #0f172a;
                padding-bottom: 3px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="section-title" style="margin-top:0;">Professional Summary</div>
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
