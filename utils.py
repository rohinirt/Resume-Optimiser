import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
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

def add_bottom_border(paragraph, color_hex="000000", size="12"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), size)
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)

def parse_markdown_formatting(text):
    """
    Parses both markdown links [Text](URL) and bold text **Text**.
    Returns a list of tuples: (content, is_bold, url_or_none)
    """
    if not text:
        return []
    
    # Combined regex pattern for links and bolding
    pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*')
    tokens = []
    last_idx = 0
    
    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            tokens.append((text[last_idx:start], False, None))
        
        link_text, link_url, bold_text = match.groups()
        if link_text is not None:
            tokens.append((link_text, False, link_url))
        elif bold_text is not None:
            tokens.append((bold_text, True, None))
            
        last_idx = end
        
    if last_idx < len(text):
        tokens.append((text[last_idx:], False, None))
        
    return tokens

def render_tokens_to_html(text):
    tokens = parse_markdown_formatting(text)
    out_html = ""
    for part, is_bold, url in tokens:
        escaped = html.escape(part)
        if url:
            out_html += f'<a href="{html.escape(url)}" target="_blank" style="color: #0000FF; text-decoration: underline;">{escaped}</a>'
        elif is_bold:
            out_html += f'<strong>{escaped}</strong>'
        else:
            out_html += escaped
    return out_html

def generate_paper_sheet_tailored_html(results):
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    
    contact = sec2.get("contact_info", {})
    cand_name = html.escape(str(contact.get("name", "ROHINI TEMBHURNIKAR")))
    cand_details = render_tokens_to_html(str(contact.get("details", "")))

    summary = render_tokens_to_html(str(sec2.get("professional_summary", "")))
    skills_grouped = sec2.get("core_competencies_grouped", {})
    exp_list = sec2.get("professional_experience", [])
    proj_list = sec2.get("projects", [])
    edu_list = sec2.get("education", [])
    cert_list = sec2.get("certifications", [])

    skills_html = ""
    for cat, val in skills_grouped.items():
        skills_html += f'<div style="margin-bottom: 4px; font-size: 0.86rem; color: #000000;"><strong>{html.escape(str(cat))}:</strong> <span style="color: #000000;">{render_tokens_to_html(str(val))}</span></div>'

    exp_html = ""
    for role in exp_list:
        role_title = render_tokens_to_html(str(role.get("role_title", "")))
        exp_html += f'<p style="font-weight: 700; color: #000000; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{role_title}</p><ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5; color: #000000;">'
        for b in role.get("bullets", []):
            exp_html += f'<li style="margin-bottom: 4px; color: #000000;">{render_tokens_to_html(b)}</li>'
        exp_html += '</ul>'

    proj_html = ""
    for proj in proj_list:
        proj_title = render_tokens_to_html(str(proj.get("project_title", "")))
        proj_html += f'<p style="font-weight: 700; color: #000000; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{proj_title}</p><ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5; color: #000000;">'
        for b in proj.get("bullets", []):
            proj_html += f'<li style="margin-bottom: 4px; color: #000000;">{render_tokens_to_html(b)}</li>'
        proj_html += '</ul>'

    edu_html = "".join([f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;">{render_tokens_to_html(str(e))}</div>' for e in edu_list])
    cert_html = "".join([f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;">{render_tokens_to_html(str(c))}</div>' for c in cert_list])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Calibri', 'Calibri Body', Arial, sans-serif;
                background-color: #ffffff;
                color: #000000;
                margin: 0;
                padding: 25px;
            }}
            .header-name {{
                font-size: 1.4rem;
                font-weight: 800;
                color: #000000;
                text-align: center;
                letter-spacing: 0.5px;
            }}
            .header-contact {{
                font-size: 0.85rem;
                color: #000000;
                text-align: center;
                margin-top: 2px;
                margin-bottom: 14px;
            }}
            .section-title {{
                color: #000000;
                font-size: 10pt;
                margin-top: 12px;
                margin-bottom: 6px;
                border-bottom: 1.5px solid #000000;
                padding-bottom: 2px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="header-name">{cand_name}</div>
        <div class="header-contact">{cand_details}</div>

        <div class="section-title">Professional Summary</div>
        <p style="font-size: 0.86rem; line-height: 1.5; color: #000000; margin-bottom: 12px;">{summary}</p>

        <div class="section-title">Work Experience</div>
        <div>{exp_html}</div>

        <div class="section-title">Projects</div>
        <div>{proj_html}</div>

        <!-- SKILLS SECTION PLACED BELOW PROJECTS -->
        <div class="section-title">Technical Skills</div>
        <div>{skills_html}</div>

        <div class="section-title">Education</div>
        <div>{edu_html}</div>

        <div class="section-title">Certifications</div>
        <div>{cert_html}</div>
    </body>
    </html>
    """

def add_hyperlink(paragraph, url, text, font_name="Calibri", font_size=Pt(9)):
    """
    Helper function to append an underlined hyperlink into a docx paragraph.
    """
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = parse_xml(f'<w:hyperlink xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" r:id="{r_id}"/>')
    new_run = parse_xml(f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')

    run_text = parse_xml(f'<w:t xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">{html.escape(text)}</w:t>')
    new_run.append(run_text)

    rPr = parse_xml(f'<w:rPr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
    color = parse_xml(f'<w:color xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="0000FF"/>')
    u = parse_xml(f'<w:u xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="single"/>')
    rPr.append(color)
    rPr.append(u)

    rFonts = parse_xml(f'<w:rFonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:ascii="{font_name}" w:hAnsi="{font_name}"/>')
    rPr.append(rFonts)

    sz = parse_xml(f'<w:sz xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="{int(font_size.pt * 2)}"/>')
    rPr.append(sz)

    new_run.append(rPr)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def add_formatted_text_to_paragraph(paragraph, text, default_font="Calibri", font_size=Pt(9)):
    tokens = parse_markdown_formatting(text)
    for part, is_bold, url in tokens:
        if url:
            add_hyperlink(paragraph, url, part, font_name=default_font, font_size=font_size)
        else:
            r = paragraph.add_run(part)
            r.font.name = default_font
            r.font.size = font_size
            r.font.bold = is_bold
            r.font.color.rgb = RGBColor(0, 0, 0)

def generate_new_formatted_docx(results):
    output = BytesIO()
    doc = docx.Document()
    sec2 = results.get("section_2_tailored_content", {})

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11.0)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)

    contact = sec2.get("contact_info", {})
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(1)
    r_name = p_name.add_run(contact.get("name", "ROHINI TEMBHURNIKAR"))
    r_name.font.name = "Calibri"
    r_name.font.size = Pt(15)
    r_name.font.bold = True
    r_name.font.color.rgb = RGBColor(0, 0, 0)

    p_contact = doc.add_paragraph()
    p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_contact.paragraph_format.space_before = Pt(0)
    p_contact.paragraph_format.space_after = Pt(8)
    add_formatted_text_to_paragraph(p_contact, contact.get("details", ""), default_font="Calibri", font_size=Pt(9))

    def add_section_header(title_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(title_text.upper())
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)  # BLACK AND BOLD HEADER
        add_bottom_border(p, color_hex="000000", size="8")
        return p

    # 1. PROFESSIONAL SUMMARY
    add_section_header("PROFESSIONAL SUMMARY")
    p_sum = doc.add_paragraph()
    p_sum.paragraph_format.space_before = Pt(0)
    p_sum.paragraph_format.space_after = Pt(6)
    add_formatted_text_to_paragraph(p_sum, sec2.get("professional_summary", ""), font_size=Pt(9))

    # 2. WORK EXPERIENCE
    add_section_header("WORK EXPERIENCE")
    for role in sec2.get("professional_experience", []):
        p_role = doc.add_paragraph()
        p_role.paragraph_format.space_before = Pt(4)
        p_role.paragraph_format.space_after = Pt(2)
        add_formatted_text_to_paragraph(p_role, role.get("role_title", "Role"), font_size=Pt(9.5))
        for b in role.get("bullets", []):
            p_b = doc.add_paragraph(style='List Bullet')
            p_b.paragraph_format.space_before = Pt(0)
            p_b.paragraph_format.space_after = Pt(2)
            add_formatted_text_to_paragraph(p_b, b.strip(), font_size=Pt(9))

    # 3. PROJECTS
    add_section_header("PROJECTS")
    for proj in sec2.get("projects", []):
        p_proj = doc.add_paragraph()
        p_proj.paragraph_format.space_before = Pt(4)
        p_proj.paragraph_format.space_after = Pt(2)
        add_formatted_text_to_paragraph(p_proj, proj.get("project_title", "Project"), font_size=Pt(9.5))
        for b in proj.get("bullets", []):
            p_b = doc.add_paragraph(style='List Bullet')
            p_b.paragraph_format.space_before = Pt(0)
            p_b.paragraph_format.space_after = Pt(2)
            add_formatted_text_to_paragraph(p_b, b.strip(), font_size=Pt(9))

    # 4. TECHNICAL SKILLS (BELOW PROJECTS)
    add_section_header("TECHNICAL SKILLS")
    for cat, val in sec2.get("core_competencies_grouped", {}).items():
        p_sk = doc.add_paragraph()
        p_sk.paragraph_format.space_before = Pt(0)
        p_sk.paragraph_format.space_after = Pt(2)
        r_cat = p_sk.add_run(f"{cat}: ")
        r_cat.font.name = "Calibri"
        r_cat.font.size = Pt(9)
        r_cat.font.bold = True
        r_cat.font.color.rgb = RGBColor(0, 0, 0)
        add_formatted_text_to_paragraph(p_sk, str(val), font_size=Pt(9))

    # 5. EDUCATION
    add_section_header("EDUCATION")
    for edu in sec2.get("education", []):
        p_edu = doc.add_paragraph()
        p_edu.paragraph_format.space_before = Pt(0)
        p_edu.paragraph_format.space_after = Pt(2)
        add_formatted_text_to_paragraph(p_edu, str(edu), font_size=Pt(9))

    # 6. CERTIFICATIONS
    add_section_header("CERTIFICATIONS")
    for cert in sec2.get("certifications", []):
        p_cert = doc.add_paragraph()
        p_cert.paragraph_format.space_before = Pt(0)
        p_cert.paragraph_format.space_after = Pt(2)
        add_formatted_text_to_paragraph(p_cert, str(cert), font_size=Pt(9))

    doc.save(output)
    output.seek(0)
    return output
