
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
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

def add_bottom_border(paragraph, color_hex="0F172A", size="12"):
    """Adds a sleek executive horizontal border line directly under section headings."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), size) # 12 = 1.5 pt line
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)

def generate_standard_resume_sheet_html(title_header, content_text_or_bytes, is_docx_file=False):
    """Renders the Original Master Resume using Arial typography and bold highlighting."""
    paragraphs_html = ""
    if is_docx_file and isinstance(content_text_or_bytes, bytes) and len(content_text_or_bytes) > 0:
        try:
            doc = docx.Document(BytesIO(content_text_or_bytes))
            for p in doc.paragraphs:
                txt = html.escape(p.text.strip())
                if txt:
                    if txt.isupper() and len(txt) < 40:
                        paragraphs_html += f'<div style="color: #1e3a8a; font-size: 0.95rem; margin-top: 14px; margin-bottom: 6px; border-bottom: 1.5px solid #0f172a; padding-bottom: 2px; font-weight: 700; text-transform: uppercase; font-family: Arial, sans-serif;">{txt}</div>'
                    else:
                        for keyword in ["Uber", "TopN Analytics", "Data Analytics Specialist", "Data Analyst Intern", "SQL", "Python", "Tableau", "Looker Studio"]:
                            if keyword in txt:
                                txt = txt.replace(keyword, f'<strong>{keyword}</strong>')
                        paragraphs_html += f'<p style="font-size: 0.88rem; line-height: 1.45; color: #334155; margin-bottom: 6px; font-family: Arial, sans-serif;">{txt}</p>'
        except Exception:
            paragraphs_html = f'<p style="font-size:0.88rem; font-family: Arial, sans-serif;">{html.escape(str(content_text_or_bytes))}</p>'
    else:
        lines = str(content_text_or_bytes).split('\n')
        for line in lines:
            txt = html.escape(line.strip())
            if txt:
                if txt.isupper() and len(txt) < 40:
                    paragraphs_html += f'<div style="color: #1e3a8a; font-size: 0.95rem; margin-top: 14px; margin-bottom: 6px; border-bottom: 1.5px solid #0f172a; padding-bottom: 2px; font-weight: 700; text-transform: uppercase; font-family: Arial, sans-serif;">{txt}</div>'
                else:
                    for keyword in ["Uber", "TopN Analytics", "Data Analytics Specialist", "Data Analyst Intern", "SQL", "Python", "Tableau", "Looker Studio"]:
                        if keyword in txt:
                            txt = txt.replace(keyword, f'<strong>{keyword}</strong>')
                    paragraphs_html += f'<p style="font-size: 0.88rem; line-height: 1.45; color: #334155; margin-bottom: 6px; font-family: Arial, sans-serif;">{txt}</p>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
                background-color: #ffffff;
                color: #1e293b;
                margin: 0;
                padding: 25px;
            }}
        </style>
    </head>
    <body>
        {paragraphs_html}
    </body>
    </html>
    """

def generate_paper_sheet_tailored_html(results):
    """Renders an executive A4-styled HTML preview document in Arial font."""
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    
    contact = sec2.get("contact_info", {})
    cand_name = html.escape(str(contact.get("name", "ROHINI TEMBHURNIKAR")))
    cand_details = html.escape(str(contact.get("details", "(+91) 8010132326 | rohinitembhurnikar3@gmail.com | Hyderabad | LinkedIn | GitHub")))

    summary = html.escape(str(sec2.get("professional_summary", "")))
    skills_grouped = sec2.get("core_competencies_grouped", {})
    exp_list = sec2.get("professional_experience", [])
    proj_list = sec2.get("projects", [])
    edu_list = sec2.get("education", [])
    cert_list = sec2.get("certifications", [])

    for kw in keywords:
        if len(kw) > 2 and kw in summary:
            escaped_kw = html.escape(kw)
            summary = summary.replace(
                escaped_kw, 
                f'<mark style="background-color: #fef08a; text-decoration: underline; padding: 1px 4px; border-radius: 3px; font-weight: 600; color: #1e293b;">{escaped_kw}</mark>'
            )

    skills_html = ""
    for cat, val in skills_grouped.items():
        skills_html += f'<div style="margin-bottom: 4px; font-size: 0.86rem;"><strong>{html.escape(str(cat))}:</strong> <span style="color: #0369a1;">{html.escape(str(val))}</span></div>'

    exp_html = ""
    for role in exp_list:
        role_title = html.escape(str(role.get("role_title", "")))
        exp_html += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{role_title}</p><ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5;">'
        for b in role.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            for kw in keywords:
                if len(kw) > 3 and kw in clean_b:
                    escaped_kw = html.escape(kw)
                    clean_b = clean_b.replace(escaped_kw, f'<mark style="background-color: #fef08a; text-decoration: underline; padding: 1px 3px; border-radius: 3px; font-weight: 600;">{escaped_kw}</mark>')
            exp_html += f'<li style="margin-bottom: 4px;">{clean_b}</li>'
        exp_html += '</ul>'

    proj_html = ""
    for proj in proj_list:
        proj_title = html.escape(str(proj.get("project_title", "")))
        proj_html += f'<p style="font-weight: 700; color: #0f172a; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{proj_title}</p><ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5;">'
        for b in proj.get("bullets", []):
            clean_b = html.escape(str(b)).replace("**", "")
            proj_html += f'<li style="margin-bottom: 4px;">{clean_b}</li>'
        proj_html += '</ul>'

    edu_html = "".join([f'<div style="font-size: 0.86rem; margin-bottom: 3px;">{html.escape(str(e))}</div>' for e in edu_list])
    cert_html = "".join([f'<div style="font-size: 0.86rem; margin-bottom: 3px;">{html.escape(str(c))}</div>' for c in cert_list])

    full_document_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
                background-color: #ffffff;
                color: #1e293b;
                margin: 0;
                padding: 25px;
            }}
            .header-name {{
                font-size: 1.4rem;
                font-weight: 800;
                color: #0f172a;
                text-align: center;
                letter-spacing: 0.5px;
            }}
            .header-contact {{
                font-size: 0.8rem;
                color: #475569;
                text-align: center;
                margin-top: 2px;
                margin-bottom: 14px;
                border-bottom: 1.5px solid #0f172a;
                padding-bottom: 8px;
            }}
            .section-title {{
                color: #1e3a8a;
                font-size: 0.92rem;
                margin-top: 12px;
                margin-bottom: 6px;
                border-bottom: 1.5px solid #0f172a;
                padding-bottom: 2px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="header-name">{cand_name}</div>
        <div class="header-contact">{cand_details}</div>

        <div class="section-title">Professional Summary</div>
        <p style="font-size: 0.86rem; line-height: 1.5; color: #334155; margin-bottom: 12px;">{summary}</p>

        <div class="section-title">Technical Skills & Competencies</div>
        <div>{skills_html}</div>

        <div class="section-title">Professional Experience</div>
        <div>{exp_html}</div>

        <div class="section-title">Key Projects</div>
        <div>{proj_html}</div>

        <div class="section-title">Education</div>
        <div>{edu_html}</div>

        <div class="section-title">Certifications</div>
        <div>{cert_html}</div>
    </body>
    </html>
    """
    return full_document_html

def replace_paragraph_text_keep_formatting(paragraph, new_text):
    if len(paragraph.runs) > 0:
        first_run = paragraph.runs[0]
        font_name = first_run.font.name or "Arial"
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
    Builds a beautifully styled 1-Page A4 Microsoft Word (.docx) Document.
    Applied settings: 0.5" Margins, Arial font, 1.5pt Section Borders, and compact spacing.
    """
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

    # IN-PLACE EDITING FOR DOCX UPLOADS
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

    # FRESH HIGH-QUALITY STYLED GENERATION FOR PDF UPLOADS
    else:
        # SET STRICT 1-PAGE A4 GEOMETRY (0.5 INCH MARGINS)
        section = doc.sections[0]
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

        # 1. CANDIDATE HEADER
        contact = sec2.get("contact_info", {})
        p_name = doc.add_paragraph()
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_name.paragraph_format.space_before = Pt(0)
        p_name.paragraph_format.space_after = Pt(1)
        r_name = p_name.add_run(contact.get("name", "ROHINI TEMBHURNIKAR"))
        r_name.font.name = "Arial"
        r_name.font.size = Pt(15)
        r_name.font.bold = True
        r_name.font.color.rgb = RGBColor(15, 23, 42)

        p_contact = doc.add_paragraph()
        p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_contact.paragraph_format.space_before = Pt(0)
        p_contact.paragraph_format.space_after = Pt(10)
        r_contact = p_contact.add_run(contact.get("details", ""))
        r_contact.font.name = "Arial"
        r_contact.font.size = Pt(8.5)
        r_contact.font.color.rgb = RGBColor(71, 85, 105)
        add_bottom_border(p_contact, color_hex="0F172A", size="12")

        def add_section_header(title_text):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(title_text.upper())
            r.font.name = "Arial"
            r.font.size = Pt(9.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 58, 138) # Navy Accent
            add_bottom_border(p, color_hex="0F172A", size="8")
            return p

        # 2. PROFESSIONAL SUMMARY
        add_section_header("PROFESSIONAL SUMMARY")
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.space_before = Pt(0)
        p_sum.paragraph_format.space_after = Pt(6)
        r_sum = p_sum.add_run(sec2.get("professional_summary", ""))
        r_sum.font.name = "Arial"
        r_sum.font.size = Pt(9)
        r_sum.font.color.rgb = RGBColor(51, 65, 85)

        # 3. TECHNICAL SKILLS
        add_section_header("TECHNICAL SKILLS")
        grouped_skills = sec2.get("core_competencies_grouped", {})
        for cat, val in grouped_skills.items():
            p_sk = doc.add_paragraph()
            p_sk.paragraph_format.space_before = Pt(0)
            p_sk.paragraph_format.space_after = Pt(2)
            
            r_cat = p_sk.add_run(f"{cat}: ")
            r_cat.font.name = "Arial"
            r_cat.font.size = Pt(9)
            r_cat.font.bold = True
            r_cat.font.color.rgb = RGBColor(15, 23, 42)

            r_val = p_sk.add_run(str(val))
            r_val.font.name = "Arial"
            r_val.font.size = Pt(9)
            r_val.font.color.rgb = RGBColor(51, 65, 85)

        # 4. WORK EXPERIENCE
        add_section_header("WORK EXPERIENCE")
        for role in sec2.get("professional_experience", []):
            p_role = doc.add_paragraph()
            p_role.paragraph_format.space_before = Pt(4)
            p_role.paragraph_format.space_after = Pt(2)
            
            r_role = p_role.add_run(role.get("role_title", "Role"))
            r_role.font.name = "Arial"
            r_role.font.size = Pt(9.5)
            r_role.font.bold = True
            r_role.font.color.rgb = RGBColor(15, 23, 42)

            for b in role.get("bullets", []):
                p_b = doc.add_paragraph()
                p_b.paragraph_format.space_before = Pt(0)
                p_b.paragraph_format.space_after = Pt(2)
                p_b.paragraph_format.left_indent = Inches(0.18)
                
                # Split markdown bolding **
                clean_bullet = b.strip()
                parts = clean_bullet.split("**")
                for idx, part in enumerate(parts):
                    if not part:
                        continue
                    r_b = p_b.add_run(part if idx % 2 == 0 else part)
                    r_b.font.name = "Arial"
                    r_b.font.size = Pt(8.8)
                    r_b.font.bold = (idx % 2 == 1)
                    r_b.font.color.rgb = RGBColor(30, 41, 59)

        # 5. KEY PROJECTS
        add_section_header("PROJECTS")
        for proj in sec2.get("projects", []):
            p_proj = doc.add_paragraph()
            p_proj.paragraph_format.space_before = Pt(4)
            p_proj.paragraph_format.space_after = Pt(2)
            
            r_proj = p_proj.add_run(proj.get("project_title", "Project"))
            r_proj.font.name = "Arial"
            r_proj.font.size = Pt(9.5)
            r_proj.font.bold = True
            r_proj.font.color.rgb = RGBColor(15, 23, 42)

            for b in proj.get("bullets", []):
                p_b = doc.add_paragraph()
                p_b.paragraph_format.space_before = Pt(0)
                p_b.paragraph_format.space_after = Pt(2)
                p_b.paragraph_format.left_indent = Inches(0.18)
                
                parts = b.strip().split("**")
                for idx, part in enumerate(parts):
                    if not part:
                        continue
                    r_b = p_b.add_run(part)
                    r_b.font.name = "Arial"
                    r_b.font.size = Pt(8.8)
                    r_b.font.bold = (idx % 2 == 1)
                    r_b.font.color.rgb = RGBColor(30, 41, 59)

        # 6. EDUCATION
        add_section_header("EDUCATION")
        for edu in sec2.get("education", []):
            p_edu = doc.add_paragraph()
            p_edu.paragraph_format.space_before = Pt(0)
            p_edu.paragraph_format.space_after = Pt(2)
            r_edu = p_edu.add_run(edu)
            r_edu.font.name = "Arial"
            r_edu.font.size = Pt(8.8)

        # 7. CERTIFICATIONS
        add_section_header("CERTIFICATIONS")
        for cert in sec2.get("certifications", []):
            p_cert = doc.add_paragraph()
            p_cert.paragraph_format.space_before = Pt(0)
            p_cert.paragraph_format.space_after = Pt(2)
            r_cert = p_cert.add_run(cert)
            r_cert.font.name = "Arial"
            r_cert.font.size = Pt(8.8)

    doc.save(output)
    output.seek(0)
    return output
