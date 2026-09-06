import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
import base64
import html
import re
from io import BytesIO
from pypdf import PdfReader

BODY_FONT = "Calibri"

def _paragraph_text_with_links(para):
    """
    Reconstruct a paragraph's visible text INCLUDING text that lives inside
    <w:hyperlink> runs (python-docx's plain .text property does not always
    include hyperlink-wrapped runs). Also returns the (display_text, url)
    pairs found, in reading order, so callers can rebuild the URLs precisely
    rather than inventing them.
    """
    parts = []
    links = []
    try:
        content_iter = para.iter_inner_content()
    except AttributeError:
        # Older python-docx without iter_inner_content: fall back to plain text.
        return para.text, []
    for item in content_iter:
        address = getattr(item, "address", None)
        if address:
            parts.append(item.text)
            links.append((item.text.strip(), address))
        else:
            parts.append(getattr(item, "text", ""))
    return "".join(parts), links

def extract_text_from_file(uploaded_file):
    """
    Extracts plain text for feeding to the LLM. For docx files, hyperlink URLs
    are appended inline right after their display text, e.g. 'LinkedIn
    (https://linkedin.com/in/...)', so the model can see and copy real URLs
    instead of ever inventing one (ZERO HALLUCINATION CONSTRAINT).
    """
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
            line, links = _paragraph_text_with_links(para)
            if links:
                for link_text, url in links:
                    if link_text:
                        line = line.replace(link_text, f"{link_text} ({url})", 1)
            text += line + "\n"
    uploaded_file.seek(0)
    return text

def extract_docx_hyperlink_map(file_or_bytes):
    """
    Returns an ordered {display_text: url} map of every hyperlink found in a
    docx file. Used to rebuild real, clickable header links (LinkedIn, GitHub,
    Portfolio, Tableau, ...) in generated previews/output, since those exact
    URLs belong to the candidate and should never be re-typed or guessed.
    """
    try:
        if isinstance(file_or_bytes, (bytes, bytearray)):
            doc = docx.Document(BytesIO(file_or_bytes))
        else:
            file_or_bytes.seek(0)
            doc = docx.Document(file_or_bytes)
            file_or_bytes.seek(0)
    except Exception:
        return {}

    link_map = {}
    for para in doc.paragraphs:
        _, links = _paragraph_text_with_links(para)
        for text, url in links:
            if text and text not in link_map:
                link_map[text] = url
    return link_map

def add_hyperlink_run(paragraph, text, url, font_name=BODY_FONT, font_size=9,
                       bold=False, color_hex="0563C1", underline=True):
    """Insert a real, clickable w:hyperlink run into a python-docx paragraph."""
    part = paragraph.part
    r_id = part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rPr.append(rFonts)

    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(int(font_size * 2)))
    rPr.append(sz)

    if bold:
        rPr.append(OxmlElement('w:b'))

    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)

    color = OxmlElement('w:color')
    color.set(qn('w:val'), color_hex)
    rPr.append(color)

    new_run.append(rPr)
    t = OxmlElement('w:t')
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink

def render_contact_line_html(details_text, hyperlink_map):
    """
    Turns a plain '(+91) ... | LinkedIn | GitHub | Portfolio | Tableau' string
    into HTML where any segment matching a known hyperlink's display text
    becomes a real, underlined, blue <a> tag using that hyperlink's real URL.
    """
    if not details_text:
        return ""
    segments = [seg.strip() for seg in details_text.split("|")]
    out_segments = []
    for seg in segments:
        url = hyperlink_map.get(seg)
        if url:
            out_segments.append(
                f'<a href="{html.escape(url)}" target="_blank" '
                f'style="color:#0563C1; text-decoration: underline;">{html.escape(seg)}</a>'
            )
        else:
            out_segments.append(html.escape(seg))
    return " | ".join(out_segments)

def add_bottom_border(paragraph, color_hex="0F172A", size="12"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), size)
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)

def clean_markdown_bold_spans(text):
    if not text:
        return []
    pattern = re.compile(r'\*\*(.*?)\*\*')
    spans = []
    last_idx = 0
    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            spans.append((text[last_idx:start], False))
        spans.append((match.group(1), True))
        last_idx = end
    if last_idx < len(text):
        remaining = text[last_idx:].replace("**", "")
        if remaining:
            spans.append((remaining, False))
    return spans

def render_spans_to_html(text):
    spans = clean_markdown_bold_spans(text)
    out_html = ""
    for part, is_bold in spans:
        escaped_part = html.escape(part)
        if is_bold:
            out_html += f'<strong>{escaped_part}</strong>'
        else:
            out_html += escaped_part
    return out_html

def generate_standard_resume_sheet_html(title_header, content_text_or_bytes, is_docx_file=False):
    hyperlink_map = {}
    if is_docx_file and isinstance(content_text_or_bytes, bytes) and len(content_text_or_bytes) > 0:
        try:
            doc = docx.Document(BytesIO(content_text_or_bytes))
            lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            hyperlink_map = extract_docx_hyperlink_map(content_text_or_bytes)
        except Exception:
            lines = []
    else:
        lines = [line.strip() for line in str(content_text_or_bytes).split('\n') if line.strip()]

    if not lines:
        return "<p>No content found.</p>"

    cand_name = html.escape(lines[0])

    # The contact/details line isn't always lines[1] — some resumes have a job-title
    # subtitle line (e.g. "Data Analyst") between the name and the contact line. Find
    # the first line that actually contains one of the known hyperlink labels (or a
    # phone/email-like pattern) and treat that as the contact line; anything in
    # between is shown as a plain subtitle line.
    contact_idx = None
    for i in range(1, min(len(lines), 5)):
        if any(label in lines[i] for label in hyperlink_map.keys()) or "@" in lines[i]:
            contact_idx = i
            break
    if contact_idx is None:
        contact_idx = 1 if len(lines) > 1 else 0

    subtitle_lines = lines[1:contact_idx]
    cand_details = render_contact_line_html(lines[contact_idx], hyperlink_map) if contact_idx < len(lines) else ""
    subtitle_html = "".join(
        f'<div class="header-subtitle">{html.escape(s)}</div>' for s in subtitle_lines
    )
    body_lines = lines[contact_idx + 1:]

    paragraphs_html = ""
    current_section = ""
    in_bullet_list = False

    for txt in body_lines:
        escaped_txt = html.escape(txt)
        if txt.isupper() and len(txt) < 40:
            if in_bullet_list:
                paragraphs_html += "</ul>"
                in_bullet_list = False
            current_section = txt.upper()
            paragraphs_html += f'<div class="section-title">{escaped_txt}</div>'
            continue

        is_bullet = txt.startswith("•") or txt.startswith("-") or txt.startswith("*") or (
            ("EXPERIENCE" in current_section or "PROJECTS" in current_section) and len(txt) > 30 and not any(k in txt for k in ["Jan 2", "Oct 2", "2026", "2025", "2024"])
        )

        if is_bullet:
            if not in_bullet_list:
                paragraphs_html += '<ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5; color: #000000;">'
                in_bullet_list = True
            clean_bullet = txt.lstrip("•-* ").strip()
            formatted_bullet = render_spans_to_html(clean_bullet)
            paragraphs_html += f'<li style="margin-bottom: 4px; color: #000000;">{formatted_bullet}</li>'
        else:
            if in_bullet_list:
                paragraphs_html += "</ul>"
                in_bullet_list = False

            if ":" in txt and ("SKILLS" in current_section or len(txt) < 80):
                parts = txt.split(":", 1)
                formatted_line = f'<strong>{html.escape(parts[0])}:</strong>{render_spans_to_html(parts[1])}'
                paragraphs_html += f'<div style="margin-bottom: 4px; font-size: 0.86rem; color: #000000;">{formatted_line}</div>'
            elif "EXPERIENCE" in current_section or "PROJECTS" in current_section:
                formatted_line = render_spans_to_html(txt)
                paragraphs_html += f'<p style="font-weight: 700; color: #000000; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{formatted_line}</p>'
            elif "EDUCATION" in current_section or "CERTIFICATIONS" in current_section:
                if "," in txt:
                    parts = txt.split(",", 1)
                    paragraphs_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;"><strong style="font-size: 9.5pt;">{html.escape(parts[0].strip())}</strong>, {html.escape(parts[1].strip())}</div>'
                else:
                    paragraphs_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;">{escaped_txt}</div>'
            else:
                formatted_line = render_spans_to_html(txt)
                paragraphs_html += f'<p style="font-size: 0.86rem; line-height: 1.5; color: #000000; margin-bottom: 12px;">{formatted_line}</p>'

    if in_bullet_list:
        paragraphs_html += "</ul>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Calibri, 'Segoe UI', Arial, sans-serif;
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
            .header-subtitle {{
                font-size: 0.95rem;
                font-weight: 700;
                color: #000000;
                text-align: center;
                margin-top: 2px;
            }}
            .header-contact {{
                font-size: 0.8rem;
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
                font-weight: 700;
                text-decoration: underline;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="header-name">{cand_name}</div>
        {subtitle_html}
        <div class="header-contact">{cand_details}</div>
        {paragraphs_html}
    </body>
    </html>
    """

def generate_paper_sheet_tailored_html(results, contact_hyperlink_map=None):
    sec2 = results.get("section_2_tailored_content", {})
    keywords = results.get("post_optimization", {}).get("matching_keywords", [])
    contact_hyperlink_map = contact_hyperlink_map or {}

    contact = sec2.get("contact_info", {})
    cand_name = html.escape(str(contact.get("name", "ROHINI TEMBHURNIKAR")))
    raw_details = str(contact.get("details", "(+91) 8010132326 | rohinitembhurnikar3@gmail.com | Hyderabad | LinkedIn | GitHub"))
    cand_details = render_contact_line_html(raw_details, contact_hyperlink_map)

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
                f'<mark style="background-color: #fef08a; text-decoration: underline; padding: 1px 4px; border-radius: 3px; font-weight: 600; color: #000000;">{escaped_kw}</mark>'
            )

    skills_html = ""
    for cat, val in skills_grouped.items():
        skills_html += f'<div style="margin-bottom: 4px; font-size: 0.86rem; color: #000000;"><strong>{html.escape(str(cat))}:</strong> <span style="color: #000000;">{html.escape(str(val))}</span></div>'

    exp_html = ""
    for role in exp_list:
        role_title = html.escape(str(role.get("role_title", "")))
        exp_html += f'<p style="font-weight: 700; color: #000000; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{role_title}</p><ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5; color: #000000;">'
        for b in role.get("bullets", []):
            formatted_b = render_spans_to_html(b)
            exp_html += f'<li style="margin-bottom: 4px; color: #000000;">{formatted_b}</li>'
        exp_html += '</ul>'

    proj_html = ""
    for proj in proj_list:
        proj_title = html.escape(str(proj.get("project_title", "")))
        proj_link = proj.get("project_link", "").strip() if proj.get("project_link") else ""
        if proj_link:
            link_label = html.escape(proj.get("project_link_label", "Link") or "Link")
            proj_title += (
                f' | <a href="{html.escape(proj_link)}" target="_blank" '
                f'style="color:#0563C1; text-decoration: underline; font-weight: 700;">{link_label}</a>'
            )
        proj_html += f'<p style="font-weight: 700; color: #000000; margin-bottom: 2px; font-size: 0.92rem; margin-top: 10px;">{proj_title}</p><ul style="margin-top: 2px; margin-bottom: 8px; padding-left: 18px; font-size: 0.86rem; line-height: 1.5; color: #000000;">'
        for b in proj.get("bullets", []):
            formatted_b = render_spans_to_html(b)
            proj_html += f'<li style="margin-bottom: 4px; color: #000000;">{formatted_b}</li>'
        proj_html += '</ul>'

    edu_html = ""
    for e in edu_list:
        txt = str(e)
        if "," in txt:
            parts = txt.split(",", 1)
            edu_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;"><strong style="font-size: 9.5pt;">{html.escape(parts[0].strip())}</strong>, {html.escape(parts[1].strip())}</div>'
        elif "|" in txt:
            parts = txt.split("|", 1)
            edu_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;"><strong style="font-size: 9.5pt;">{html.escape(parts[0].strip())}</strong> | {html.escape(parts[1].strip())}</div>'
        else:
            edu_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;">{html.escape(txt)}</div>'

    cert_html = ""
    for c in cert_list:
        txt = str(c)
        if "," in txt:
            parts = txt.split(",", 1)
            cert_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;"><strong style="font-size: 9.5pt;">{html.escape(parts[0].strip())}</strong>, {html.escape(parts[1].strip())}</div>'
        elif "|" in txt:
            parts = txt.split("|", 1)
            cert_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;"><strong style="font-size: 9.5pt;">{html.escape(parts[0].strip())}</strong> | {html.escape(parts[1].strip())}</div>'
        else:
            cert_html += f'<div style="font-size: 0.86rem; margin-bottom: 3px; color: #000000;">{html.escape(txt)}</div>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Calibri, 'Segoe UI', Arial, sans-serif;
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
                font-size: 0.8rem;
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
                font-weight: 700;
                text-decoration: underline;
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

        <div class="section-title">Skills</div>
        <div>{skills_html}</div>

        <div class="section-title">Education</div>
        <div>{edu_html}</div>

        <div class="section-title">Certifications</div>
        <div>{cert_html}</div>
    </body>
    </html>
    """

def generate_new_formatted_docx(results, contact_hyperlink_map=None):
    output = BytesIO()
    doc = docx.Document()
    sec2 = results.get("section_2_tailored_content", {})
    contact_hyperlink_map = contact_hyperlink_map or {}

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
    r_name.font.name = BODY_FONT
    r_name.font.size = Pt(15)
    r_name.font.bold = True
    r_name.font.color.rgb = RGBColor(0, 0, 0)

    p_contact = doc.add_paragraph()
    p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_contact.paragraph_format.space_before = Pt(0)
    p_contact.paragraph_format.space_after = Pt(8)
    contact_details = contact.get("details", "")
    contact_segments = [seg.strip() for seg in contact_details.split("|")] if contact_details else []
    for i, seg in enumerate(contact_segments):
        if i > 0:
            r_sep = p_contact.add_run(" | ")
            r_sep.font.name = BODY_FONT
            r_sep.font.size = Pt(9)
            r_sep.font.color.rgb = RGBColor(0, 0, 0)
        url = contact_hyperlink_map.get(seg)
        if url:
            add_hyperlink_run(p_contact, seg, url, font_name=BODY_FONT, font_size=9,
                               color_hex="0563C1", underline=True)
        else:
            r_seg = p_contact.add_run(seg)
            r_seg.font.name = BODY_FONT
            r_seg.font.size = Pt(9)
            r_seg.font.color.rgb = RGBColor(0, 0, 0)

    def add_section_header(title_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(title_text.upper())
        r.font.name = BODY_FONT
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.underline = True
        r.font.color.rgb = RGBColor(0, 0, 0)
        return p

    add_section_header("PROFESSIONAL SUMMARY")
    p_sum = doc.add_paragraph()
    p_sum.paragraph_format.space_before = Pt(0)
    p_sum.paragraph_format.space_after = Pt(6)
    for part, is_bold in clean_markdown_bold_spans(sec2.get("professional_summary", "")):
        r_sum = p_sum.add_run(part)
        r_sum.font.name = BODY_FONT
        r_sum.font.size = Pt(9)
        r_sum.font.bold = is_bold
        r_sum.font.color.rgb = RGBColor(0, 0, 0)

    add_section_header("WORK EXPERIENCE")
    for role in sec2.get("professional_experience", []):
        p_role = doc.add_paragraph()
        p_role.paragraph_format.space_before = Pt(4)
        p_role.paragraph_format.space_after = Pt(2)
        r_role = p_role.add_run(role.get("role_title", "Role"))
        r_role.font.name = BODY_FONT
        r_role.font.size = Pt(9.5)
        r_role.font.bold = True
        r_role.font.color.rgb = RGBColor(0, 0, 0)
        for b in role.get("bullets", []):
            p_b = doc.add_paragraph(style='List Bullet')
            p_b.paragraph_format.space_before = Pt(0)
            p_b.paragraph_format.space_after = Pt(2)
            for part, is_bold in clean_markdown_bold_spans(b.strip()):
                r_b = p_b.add_run(part)
                r_b.font.name = BODY_FONT
                r_b.font.size = Pt(9)
                r_b.font.bold = is_bold
                r_b.font.color.rgb = RGBColor(0, 0, 0)

    add_section_header("PROJECTS")
    for proj in sec2.get("projects", []):
        p_proj = doc.add_paragraph()
        p_proj.paragraph_format.space_before = Pt(4)
        p_proj.paragraph_format.space_after = Pt(2)
        r_proj = p_proj.add_run(proj.get("project_title", "Project"))
        r_proj.font.name = BODY_FONT
        r_proj.font.size = Pt(9.5)
        r_proj.font.bold = True
        r_proj.font.color.rgb = RGBColor(0, 0, 0)
        proj_link = (proj.get("project_link") or "").strip()
        if proj_link:
            r_sep = p_proj.add_run(" | ")
            r_sep.font.name = BODY_FONT
            r_sep.font.size = Pt(9.5)
            r_sep.font.color.rgb = RGBColor(0, 0, 0)
            link_label = proj.get("project_link_label") or "Link"
            add_hyperlink_run(p_proj, link_label, proj_link, font_name=BODY_FONT,
                               font_size=9.5, bold=True, color_hex="0563C1", underline=True)
        for b in proj.get("bullets", []):
            p_b = doc.add_paragraph(style='List Bullet')
            p_b.paragraph_format.space_before = Pt(0)
            p_b.paragraph_format.space_after = Pt(2)
            for part, is_bold in clean_markdown_bold_spans(b.strip()):
                r_b = p_b.add_run(part)
                r_b.font.name = BODY_FONT
                r_b.font.size = Pt(9)
                r_b.font.bold = is_bold
                r_b.font.color.rgb = RGBColor(0, 0, 0)

    add_section_header("SKILLS")
    for cat, val in sec2.get("core_competencies_grouped", {}).items():
        p_sk = doc.add_paragraph()
        p_sk.paragraph_format.space_before = Pt(0)
        p_sk.paragraph_format.space_after = Pt(2)
        r_cat = p_sk.add_run(f"{cat}: ")
        r_cat.font.name = BODY_FONT
        r_cat.font.size = Pt(9)
        r_cat.font.bold = True
        r_cat.font.color.rgb = RGBColor(0, 0, 0)
        r_val = p_sk.add_run(str(val))
        r_val.font.name = BODY_FONT
        r_val.font.size = Pt(9)
        r_val.font.color.rgb = RGBColor(0, 0, 0)

    add_section_header("EDUCATION")
    for edu in sec2.get("education", []):
        p_edu = doc.add_paragraph()
        p_edu.paragraph_format.space_before = Pt(0)
        p_edu.paragraph_format.space_after = Pt(2)
        txt = str(edu)
        if "," in txt:
            parts = txt.split(",", 1)
            r_deg = p_edu.add_run(parts[0].strip())
            r_deg.font.name = BODY_FONT
            r_deg.font.size = Pt(9.5)
            r_deg.font.bold = True
            r_deg.font.color.rgb = RGBColor(0, 0, 0)
            r_rest = p_edu.add_run(f", {parts[1].strip()}")
            r_rest.font.name = BODY_FONT
            r_rest.font.size = Pt(9)
            r_rest.font.color.rgb = RGBColor(0, 0, 0)
        elif "|" in txt:
            parts = txt.split("|", 1)
            r_deg = p_edu.add_run(parts[0].strip())
            r_deg.font.name = BODY_FONT
            r_deg.font.size = Pt(9.5)
            r_deg.font.bold = True
            r_deg.font.color.rgb = RGBColor(0, 0, 0)
            r_rest = p_edu.add_run(f" | {parts[1].strip()}")
            r_rest.font.name = BODY_FONT
            r_rest.font.size = Pt(9)
            r_rest.font.color.rgb = RGBColor(0, 0, 0)
        else:
            r_deg = p_edu.add_run(txt)
            r_deg.font.name = BODY_FONT
            r_deg.font.size = Pt(9)
            r_deg.font.color.rgb = RGBColor(0, 0, 0)

    add_section_header("CERTIFICATIONS")
    for cert in sec2.get("certifications", []):
        p_cert = doc.add_paragraph()
        p_cert.paragraph_format.space_before = Pt(0)
        p_cert.paragraph_format.space_after = Pt(2)
        txt = str(cert)
        if "," in txt:
            parts = txt.split(",", 1)
            r_cert = p_cert.add_run(parts[0].strip())
            r_cert.font.name = BODY_FONT
            r_cert.font.size = Pt(9.5)
            r_cert.font.bold = True
            r_cert.font.color.rgb = RGBColor(0, 0, 0)
            r_rest = p_cert.add_run(f", {parts[1].strip()}")
            r_rest.font.name = BODY_FONT
            r_rest.font.size = Pt(9)
            r_rest.font.color.rgb = RGBColor(0, 0, 0)
        elif "|" in txt:
            parts = txt.split("|", 1)
            r_cert = p_cert.add_run(parts[0].strip())
            r_cert.font.name = BODY_FONT
            r_cert.font.size = Pt(9.5)
            r_cert.font.bold = True
            r_cert.font.color.rgb = RGBColor(0, 0, 0)
            r_rest = p_cert.add_run(f" | {parts[1].strip()}")
            r_rest.font.name = BODY_FONT
            r_rest.font.size = Pt(9)
            r_rest.font.color.rgb = RGBColor(0, 0, 0)
        else:
            r_cert = p_cert.add_run(txt)
            r_cert.font.name = BODY_FONT
            r_cert.font.size = Pt(9)
            r_cert.font.color.rgb = RGBColor(0, 0, 0)

    doc.save(output)
    output.seek(0)
    return output
