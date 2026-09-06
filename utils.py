import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import html
import re
from io import BytesIO
from pypdf import PdfReader


# ============================================================
# RESUME FORMAT — SOURCE OF TRUTH
# ============================================================
# Based on the uploaded reference resume:
#
# Page: A4
# Top margin: 0.6 inch
# Other margins: 1 cm
# Font: Calibri
# Name: 20 pt
# Job title: 10 pt
# Contact: 9 pt
# Section headlines: 11 pt
# Experience/project titles: 10 pt
# Body/bullets: 9 pt
# Text: black
#
# The project URLs below were extracted from the uploaded
# PROJECTS_DESCRIPTION document. Keep this dictionary updated
# if project URLs change.
# ============================================================

FONT_NAME = "Calibri"

PAGE_WIDTH_IN = 8.268
PAGE_HEIGHT_IN = 11.693

TOP_MARGIN_IN = 0.60
SIDE_MARGIN_IN = 1 / 2.54  # 1 cm
BOTTOM_MARGIN_IN = 1 / 2.54  # 1 cm

NAME_SIZE = 20
TITLE_SIZE = 10
CONTACT_SIZE = 9
HEADLINE_SIZE = 11
ENTRY_TITLE_SIZE = 10
BODY_SIZE = 9

BLACK = RGBColor(0, 0, 0)


# Contact links from the uploaded reference resume.
CONTACT_LINKS = {
    "LinkedIn": "https://www.linkedin.com/in/rohinitembhurnikar/",
    "GitHub": "https://github.com/rohinirt",
    "Portfolio": "https://rohinisportfolio.godaddysites.com/home",
    "Tableau": "https://public.tableau.com/app/profile/rohini.tembhurnikar/vizzes",
}


# Project links from PROJECTS_DESCRIPTION(2).docx.
# The matching is intentionally based on project title, so the
# AI can return a slightly different surrounding description
# without losing the project URL.
PROJECT_LINKS = {
    "LinkedIn Job Market Analysis (2023)": "https://github.com/rohinirt/Python_Projects/blob/main/Linkedin_jobs.ipynb",
    "House Price Prediction": "https://github.com/rohinirt/Python_Projects/blob/main/House_Price_Prediction.ipynb",
    "Amazon Product Review Sentiment Analysis": "https://github.com/rohinirt/Python_Projects/blob/main/Amazon_Review_analysis.ipynb",
    "Zepto Product Data – Exploratory Data Analysis (EDA)": "https://github.com/rohinirt/Python_Projects/tree/main/Zepto%20Inventory%20-%20EDA",
    "Retail Price Optimization": "https://github.com/rohinirt/Python_Projects/tree/main/Case%20Study%3A%20Retail%20Price%20Optimization",
    "Customer Lifetime Value (CLTV) Analysis": "https://github.com/rohinirt/Python_Projects/tree/main/Customer%20Lifetime%20Value%20Analysis",
    "Supply Chain Dashboard": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/SupplyChain_17034125066550/PRODUCTS",
    "NSE Stock Analysis": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/Top15NSEStocksbyMarketCapitalization/NSEStocks",
    "Employee Performance Dashboard": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/HRDashboard_17043083751860/MetrixOverview",
    "Merchandise Sales Dashboard": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/MerchaniseSales/PRODUCTS",
    "Fitness Business Financial Performance Dashboard": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/FitnessFinance_17239202454140/Dashboard1",
    "Healthcare Operations Dashboard": "https://app.powerbi.com/view?r=eyJrIjoiMTI0ZmUwMzktMTAwMi00YzFjLTk1MDMtYjc1ZDdjMmU3ZWNiIiwidCI6ImMwZDdmYjJmLTczZDItNDA5NC1iNzY5LTFkZTQ0NDNlNzg5YiJ9",
    "Cab Rides Analysis Dashboard": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/OlaRides/OVERVIEW",
    "Pune Uber Trips Analysis": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/UberDashboard_17397212991330/Dashboard1",
    "Bike Sales in Europe": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/BikeSalesinEurope_17800428612320/Overview",
    "Amazon Stock Market Trends": "https://public.tableau.com/app/profile/rohini.tembhurnikar/viz/AmazonStockMarketTrends_17800442486380/Dashboard1",
    "HR Employee Attrition Dashboard": "https://lookerstudio.google.com/u/0/reporting/f193c501-d56b-41e1-8c03-4a6c7df4ed82/page/p_gc4ab9skvd",
    "Instacart Market Basket Analysis": "https://github.com/rohinirt/SQL_Projects/tree/main/Instacart_Market_Basket_Analysis",
    "Customer Segmentation": "https://github.com/rohinirt/SQL_Projects/tree/main/Customer-Segmentation",
    "Fraud Detection Analysis": "https://github.com/rohinirt/Fraud_Detection",
    "Music Store Analysis": "https://github.com/rohinirt/Music_stotre_SQL",
    "YouTube Trending Video Analysis": "https://github.com/rohinirt/SQL_Projects/tree/main/YouTube%20Top%20200%20Trending%20Video%20Analysis",
    "Pizza Hut Sales Analysis": "https://github.com/rohinirt/SQL_Projects/tree/main/Pizza%20Sales",
    "Spotify Songs Analysis": "https://github.com/rohinirt/SQL_Projects/tree/main/Spotify_Analysis",
    "Social Media Content Performance": "https://app.powerbi.com/view?r=eyJrIjoiZGU5NDI2MmItY2Y2OC00YTcwLTkzMjktNWRhYTAzNTc5YjM2IiwidCI6ImMwZDdmYjJmLTczZDItNDA5NC1iNzY5LTFkZTQ0NDNlNzg5YiJ9",
    "Automated ATS Job Tracker & Real-Time Telegram Alert System": "https://github.com/rohinirt/Data_Analyst_Job_Alert",
    "ResumeAlign AI": "https://resume-optimiser-pc5dxc3qh5b3cd3ldiijxq.streamlit.app/",
    # This project exists in the source file but has no hyperlink there.
    "Customer Churn Analysis": None,
}


def extract_text_from_file(uploaded_file):
    """Extract plain text while keeping the existing app API unchanged."""
    if not uploaded_file:
        return ""

    text = ""
    uploaded_file.seek(0)

    if uploaded_file.name.lower().endswith(".pdf"):
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"

    elif uploaded_file.name.lower().endswith(".docx"):
        document = docx.Document(uploaded_file)
        for para in document.paragraphs:
            text += para.text + "\n"

    uploaded_file.seek(0)
    return text


def normalize_text(value):
    """Normalize titles for robust project-link matching."""
    if value is None:
        return ""

    value = str(value)
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[|]+$", "", value)
    return value.strip().lower()


def get_project_url(project_title):
    """
    Return the project URL associated with the selected project.
    Matching is tolerant of minor punctuation/spacing differences.
    """
    title = normalize_text(project_title)

    if not title:
        return None

    # Exact normalized match first.
    for known_title, url in PROJECT_LINKS.items():
        if normalize_text(known_title) == title:
            return url

    # Then allow one title to contain the other.
    for known_title, url in PROJECT_LINKS.items():
        known = normalize_text(known_title)
        if known and (known in title or title in known):
            return url

    return None


def add_bottom_border(paragraph, color_hex="000000", size="8", space="3"):
    """Add a black bottom rule to a Word paragraph."""
    pPr = paragraph._p.get_or_add_pPr()

    # Remove existing paragraph borders so repeated calls don't stack them.
    existing = pPr.find(qn("w:pBdr"))
    if existing is not None:
        pPr.remove(existing)

    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), space)
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def clean_markdown_bold_spans(text):
    """
    Convert Gemini-style **bold** markers into (text, is_bold) spans.
    """
    if not text:
        return []

    pattern = re.compile(r"\*\*(.*?)\*\*", re.DOTALL)
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
    """Render Gemini markdown bold into HTML <strong> tags."""
    out_html = ""

    for part, is_bold in clean_markdown_bold_spans(text):
        escaped = html.escape(part)
        if is_bold:
            out_html += f"<strong>{escaped}</strong>"
        else:
            out_html += escaped

    return out_html


def add_docx_run(paragraph, text, size=BODY_SIZE, bold=False, italic=False):
    """Add a consistently formatted Calibri run."""
    run = paragraph.add_run(str(text))
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = BLACK

    # Explicitly set eastAsia/complexScript font names too.
    rPr = run._r.get_or_add_rPr()

    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)

    rFonts.set(qn("w:ascii"), FONT_NAME)
    rFonts.set(qn("w:hAnsi"), FONT_NAME)
    rFonts.set(qn("w:eastAsia"), FONT_NAME)
    rFonts.set(qn("w:cs"), FONT_NAME)

    return run


def add_docx_hyperlink(paragraph, text, url, size=CONTACT_SIZE, bold=False):
    """Create a clickable hyperlink in a DOCX without changing its black appearance."""
    if not url:
        return add_docx_run(paragraph, text, size=size, bold=bold)

    part = paragraph.part
    relationship_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), FONT_NAME)
    rFonts.set(qn("w:hAnsi"), FONT_NAME)
    rFonts.set(qn("w:eastAsia"), FONT_NAME)
    rFonts.set(qn("w:cs"), FONT_NAME)
    rPr.append(rFonts)

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    rPr.append(sz)

    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    rPr.append(color)

    # The reference resume displays hyperlinks underlined.
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    rPr.append(underline)

    if bold:
        b = OxmlElement("w:b")
        rPr.append(b)

    new_run.append(rPr)

    text_node = OxmlElement("w:t")
    text_node.text = str(text)
    new_run.append(text_node)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return hyperlink


def add_bold_spans_to_docx(paragraph, text, size=BODY_SIZE):
    """Add text containing **bold** markers to a Word paragraph."""
    for part, is_bold in clean_markdown_bold_spans(str(text).strip()):
        if part:
            add_docx_run(paragraph, part, size=size, bold=is_bold)


def add_resume_bullet_docx(doc, text):
    """Add the compact bullet used throughout the reference resume."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.left_indent = Inches(0.20)
    p.paragraph_format.first_line_indent = Inches(-0.15)

    add_docx_run(p, "• ", size=BODY_SIZE)
    add_bold_spans_to_docx(p, text, size=BODY_SIZE)

    return p


def add_section_header_docx(doc, title):
    """11 pt bold, black, uppercase, underlined section heading."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True

    run = add_docx_run(
        p,
        str(title).upper(),
        size=HEADLINE_SIZE,
        bold=True,
    )
    run.underline = True

    return p



def add_contact_line_docx(doc, contact_details):
    """
    Build the contact line while preserving clickable links.
    Known link labels are converted into real Word hyperlinks.
    """
    details = str(contact_details or "").strip()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15

    # Split only on known link labels so phone/email/location remain plain text.
    labels = list(CONTACT_LINKS.keys())
    pattern = re.compile("(" + "|".join(re.escape(x) for x in labels) + ")")

    parts = pattern.split(details)

    for part in parts:
        if not part:
            continue

        if part in CONTACT_LINKS:
            add_docx_hyperlink(
                p,
                part,
                CONTACT_LINKS[part],
                size=CONTACT_SIZE,
            )
        else:
            add_docx_run(p, part, size=CONTACT_SIZE)

    return p



def _docx_paragraph_is_bullet(paragraph):
    """
    Detect Word list formatting. Word list bullets are often stored in
    numbering properties rather than as a literal bullet character.
    """
    style_name = ""
    try:
        style_name = paragraph.style.name or ""
    except Exception:
        pass

    if "List" in style_name or "Bullet" in style_name:
        return True

    pPr = paragraph._p.pPr
    if pPr is not None and pPr.numPr is not None:
        return True

    return False


def _docx_paragraph_to_html(paragraph):
    """
    Preserve bold runs and real hyperlinks from the uploaded DOCX.
    """
    pieces = []

    for child in paragraph._p:
        if child.tag == qn("w:hyperlink"):
            rid = child.get(qn("r:id"))
            url = None
            if rid and rid in paragraph.part.rels:
                url = paragraph.part.rels[rid].target_ref

            link_runs = child.xpath(".//w:r")
            link_text = ""
            link_bold = False

            for run_el in link_runs:
                link_text += "".join(run_el.xpath(".//w:t/text()"))
                if run_el.xpath(".//w:b"):
                    link_bold = True

            if url:
                style = "font-weight:700;" if link_bold else ""
                pieces.append(
                    f'<a href="{html.escape(url, quote=True)}" '
                    f'target="_blank" rel="noopener noreferrer" '
                    f'style="color:#000000;text-decoration:underline;{style}">'
                    f'{html.escape(link_text)}</a>'
                )
            else:
                pieces.append(html.escape(link_text))

        elif child.tag == qn("w:r"):
            texts = child.xpath(".//w:t/text()")
            if not texts:
                continue

            value = "".join(texts)
            run_text = html.escape(value)

            if child.xpath(".//w:b"):
                run_text = f"<strong>{run_text}</strong>"

            pieces.append(run_text)

    return "".join(pieces) if pieces else html.escape(paragraph.text or "")


def generate_standard_resume_sheet_html(title_header, content_text_or_bytes, is_docx_file=False):
    """
    Render the uploaded resume as an A4-ratio preview.

    For DOCX input, preserve:
    - real hyperlinks
    - bold runs
    - underlined section headings
    - Word list/numbering bullets
    """
    paragraphs = []

    if is_docx_file and isinstance(content_text_or_bytes, bytes) and content_text_or_bytes:
        try:
            document = docx.Document(BytesIO(content_text_or_bytes))
            for p in document.paragraphs:
                if p.text.strip() or _docx_paragraph_is_bullet(p):
                    paragraphs.append(("docx", p))
        except Exception:
            paragraphs = []

    if not paragraphs:
        lines = [
            line.strip()
            for line in str(content_text_or_bytes).splitlines()
            if line.strip()
        ]
        paragraphs = [("text", line) for line in lines]

    if not paragraphs:
        return "<p>No content found.</p>"

    first_text = paragraphs[0][1].text if paragraphs[0][0] == "docx" else paragraphs[0][1]
    second_text = paragraphs[1][1].text if len(paragraphs) > 1 and paragraphs[1][0] == "docx" else (
        paragraphs[1][1] if len(paragraphs) > 1 else ""
    )
    third_text = paragraphs[2][1].text if len(paragraphs) > 2 and paragraphs[2][0] == "docx" else (
        paragraphs[2][1] if len(paragraphs) > 2 else ""
    )

    body = paragraphs[3:] if len(paragraphs) > 3 else []

    def paragraph_to_html(item):
        kind, value = item
        if kind == "text":
            return render_spans_to_html(value)
        return _docx_paragraph_to_html(value)

    # Render the contact line with the actual hyperlinks from the uploaded DOCX.
    if paragraphs and paragraphs[2][0] == "docx":
        contact_html = _docx_paragraph_to_html(paragraphs[2][1])
    else:
        contact_html = html.escape(third_text)

    body_html = ""
    current_section = ""

    section_names = {
        "PROFESSIONAL SUMMARY",
        "EXPERIENCE",
        "PROJECTS",
        "SKILLS",
        "EDUCATION",
        "CERTIFICATIONS",
    }

    for item in body:
        text_value = item[1].text if item[0] == "docx" else str(item[1])
        stripped = text_value.strip()

        if not stripped and not (item[0] == "docx" and _docx_paragraph_is_bullet(item[1])):
            continue

        upper = stripped.upper()

        if upper in section_names:
            current_section = upper
            body_html += f'<div class="section-title">{html.escape(upper)}</div>'
            continue

        rendered = paragraph_to_html(item)
        is_bullet = (
            (item[0] == "docx" and _docx_paragraph_is_bullet(item[1]))
            or stripped.startswith(("•", "", "-", "*"))
        )

        if is_bullet:
            # Word stores the bullet in numbering properties, not paragraph.text.
            # Add the visual bullet explicitly in HTML.
            body_html += (
                f'<div class="bullet"><span class="bullet-mark">•</span>'
                f'{rendered}</div>'
            )

        elif current_section in ("EXPERIENCE", "PROJECTS"):
            body_html += f'<div class="entry-title">{rendered}</div>'

        else:
            body_html += f'<div class="body-text">{rendered}</div>'

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{
        box-sizing: border-box;
    }}

    html, body {{
        margin: 0;
        padding: 0;
        background: #ffffff;
    }}

    body {{
        font-family: Calibri, sans-serif;
        color: #000000;
        font-size: 9pt;
    }}

    .resume-page {{
        width: 100%;
        max-width: 210mm;
        aspect-ratio: 210 / 297;
        padding: 0.6in 1cm 1cm 1cm;
        margin: 0 auto;
        background: #ffffff;
        overflow: hidden;
    }}

    .header-name {{
        font-size: 20pt;
        font-weight: 400;
        text-align: center;
        line-height: 1;
        margin: 0;
    }}

    .header-title {{
        font-size: 10pt;
        font-weight: 700;
        text-align: center;
        line-height: 1.1;
        margin: 0;
    }}

    .header-contact {{
        font-size: 9pt;
        font-weight: 400;
        text-align: center;
        line-height: 1.1;
        margin: 0;
    }}

    .header-contact a,
    a {{
        color: #000000;
        text-decoration: underline;
    }}

    .section-title {{
        font-size: 11pt;
        font-weight: 700;
        line-height: 1;
        margin-top: 4pt;
        margin-bottom: 2pt;
        color: #000000;
        text-transform: uppercase;
        text-decoration: underline;
    }}

    .body-text {{
        font-size: 9pt;
        line-height: 1.15;
        margin: 0;
        color: #000000;
    }}

    .entry-title {{
        font-size: 10pt;
        line-height: 1.1;
        font-weight: 700;
        margin: 1pt 0 0 0;
        color: #000000;
    }}

    .bullet {{
        font-size: 9pt;
        line-height: 1.15;
        margin: 0;
        padding-left: 12px;
        text-indent: 0;
        color: #000000;
    }}

    .bullet-mark {{
        display: inline-block;
        width: 9px;
        margin-left: -12px;
        margin-right: 3px;
    }}

    strong {{
        font-weight: 700;
    }}
</style>
</head>
<body>
<div class="resume-page">
    <div class="header-name">{html.escape(first_text)}</div>
    <div class="header-title">{html.escape(second_text)}</div>
    <div class="header-contact">{contact_html}</div>
    {body_html}
</div>
</body>
</html>
"""



def render_summary_with_keywords_html(summary, keywords):
    """
    Render existing **bold** spans and additionally bold matching JD keywords.
    This does not add highlighting/backgrounds; it only uses normal bold text.
    """
    pieces = clean_markdown_bold_spans(str(summary or ""))
    keywords = sorted(
        {str(k).strip() for k in (keywords or []) if str(k).strip()},
        key=len,
        reverse=True,
    )

    out = []
    for part, already_bold in pieces:
        if not part:
            continue

        if already_bold or not keywords:
            escaped = html.escape(part)
            out.append(f"<strong>{escaped}</strong>" if already_bold else escaped)
            continue

        # Bold exact keyword phrases, case-insensitively, without changing
        # punctuation or capitalization.
        pattern = re.compile(
            "(" + "|".join(re.escape(k) for k in keywords) + ")",
            flags=re.IGNORECASE,
        )

        last = 0
        for match in pattern.finditer(part):
            out.append(html.escape(part[last:match.start()]))
            out.append(f"<strong>{html.escape(match.group(0))}</strong>")
            last = match.end()

        out.append(html.escape(part[last:]))

    return "".join(out)


def add_summary_with_keywords_docx(paragraph, summary, keywords):
    """
    Render summary bold markers and JD matching keywords as normal bold text.
    """
    pieces = clean_markdown_bold_spans(str(summary or ""))
    keywords = sorted(
        {str(k).strip() for k in (keywords or []) if str(k).strip()},
        key=len,
        reverse=True,
    )

    for part, already_bold in pieces:
        if not part:
            continue

        if already_bold or not keywords:
            add_docx_run(paragraph, part, size=BODY_SIZE, bold=already_bold)
            continue

        pattern = re.compile(
            "(" + "|".join(re.escape(k) for k in keywords) + ")",
            flags=re.IGNORECASE,
        )

        last = 0
        for match in pattern.finditer(part):
            if match.start() > last:
                add_docx_run(
                    paragraph,
                    part[last:match.start()],
                    size=BODY_SIZE,
                    bold=False,
                )
            add_docx_run(
                paragraph,
                match.group(0),
                size=BODY_SIZE,
                bold=True,
            )
            last = match.end()

        if last < len(part):
            add_docx_run(
                paragraph,
                part[last:],
                size=BODY_SIZE,
                bold=False,
            )


def _contact_html(contact_details):
    """Render contact details with clickable known links."""
    details = str(contact_details or "").strip()

    labels = list(CONTACT_LINKS.keys())
    pattern = re.compile("(" + "|".join(re.escape(x) for x in labels) + ")")

    parts = pattern.split(details)
    out = []

    for part in parts:
        if not part:
            continue

        if part in CONTACT_LINKS:
            url = CONTACT_LINKS[part]
            out.append(
                f'<a href="{html.escape(url, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">{html.escape(part)}</a>'
            )
        else:
            out.append(html.escape(part))

    return "".join(out)


def _project_title_html(project_title):
    """
    Render project title and its clickable Link.
    The AI does not need to generate the URL itself.
    """
    title = str(project_title or "").strip()
    url = get_project_url(title)

    # If the title already contains a Link/GitHub token, remove it
    # and add our controlled hyperlink at the end.
    cleaned_title = re.sub(
        r"\s*\|\s*(?:Link|GitHub)\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    title_html = render_spans_to_html(cleaned_title)

    if url:
        return (
            f'{title_html} <span class="separator">|</span> '
            f'<a class="project-link" href="{html.escape(url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">Link</a>'
        )

    return title_html


def _project_title_docx(doc, project_title):
    """Render a 10 pt bold project title and an underlined clickable Link."""
    title = str(project_title or "").strip()

    cleaned_title = re.sub(
        r"\s*\|\s*(?:Link|GitHub)\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True

    # Reference resume uses a bold 10 pt project name.
    add_docx_run(p, cleaned_title, size=ENTRY_TITLE_SIZE, bold=True)

    url = get_project_url(title)

    if url:
        add_docx_run(p, " | ", size=BODY_SIZE, bold=False)
        add_docx_hyperlink(p, "Link", url, size=BODY_SIZE, bold=False)

    return p



def split_title_and_details(text):
    """
    Return (title, details) for education/certification lines.

    Reference resume behavior:
    - Education: degree name is bold; institution/date are regular.
    - Certification: certification name is bold; provider/date are regular.
    """
    value = str(text or "").strip()

    if "|" in value:
        first, details = value.split("|", 1)
        first = first.strip()
        details = details.strip()

        # Gemini sometimes returns:
        # "Master of Computer Application, SNDT University Mumbai (80%) | May 2025"
        # In that form, only the degree/certificate title should be bold.
        if "," in first:
            title = first.split(",", 1)[0].strip()
            remainder = first[len(first.split(",", 1)[0]):].strip()
            if remainder:
                details = remainder + " | " + details

            return title, details

        return first, details

    # If there is no pipe, keep the whole line as the title.
    return value, ""



def education_html(items):
    out = ""
    for item in items or []:
        title, details = split_title_and_details(item)
        if details:
            out += (
                '<div class="body-text">'
                f'<strong>{render_spans_to_html(title)}</strong> | '
                f'{render_spans_to_html(details)}'
                '</div>'
            )
        elif title:
            out += f'<div class="body-text"><strong>{render_spans_to_html(title)}</strong></div>'
    return out


def certification_html(items):
    out = ""
    for item in items or []:
        title, details = split_title_and_details(item)
        if details:
            out += (
                '<div class="body-text">'
                f'<strong>{render_spans_to_html(title)}</strong> | '
                f'{render_spans_to_html(details)}'
                '</div>'
            )
        elif title:
            out += f'<div class="body-text"><strong>{render_spans_to_html(title)}</strong></div>'
    return out


def add_title_details_docx(doc, text):
    """
    Add an education/certification line with its title bolded.
    """
    title, details = split_title_and_details(text)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15

    if title:
        add_bold_spans_to_docx(p, title, size=BODY_SIZE)
        # The title itself should be bold even if Gemini omitted **.
        for run in p.runs:
            run.bold = True

    if details:
        add_docx_run(p, " | ", size=BODY_SIZE)
        add_bold_spans_to_docx(p, details, size=BODY_SIZE)

    return p


def generate_paper_sheet_tailored_html(results):
    """
    Optimized A4 resume preview.
    Preview order:
    Summary → Experience → Projects → Skills → Education → Certifications.
    """
    sec2 = results.get("section_2_tailored_content", {}) or {}

    contact = sec2.get("contact_info", {}) or {}
    cand_name = str(contact.get("name", "Rohini Tembhurnikar")).strip()
    cand_details = str(
        contact.get(
            "details",
            "(+91) 8010132326 | rohinitembhurnikar3@gmail.com | "
            "Hyderabad, India | LinkedIn | GitHub | Portfolio | Tableau",
        )
    ).strip()

    summary = str(sec2.get("professional_summary", "")).strip()
    keywords = results.get("post_optimization", {}).get("matching_keywords", []) or []
    skills_grouped = sec2.get("core_competencies_grouped", {}) or {}
    exp_list = sec2.get("professional_experience", []) or []
    proj_list = sec2.get("projects", []) or []
    edu_list = sec2.get("education", []) or []
    cert_list = sec2.get("certifications", []) or []

    skills_html = ""
    for cat, val in skills_grouped.items():
        skills_html += (
            '<div class="skill-line">'
            f'<strong>{html.escape(str(cat))}:</strong> '
            f'{render_spans_to_html(str(val))}'
            '</div>'
        )

    exp_html = ""
    for role in exp_list:
        role_title = str(role.get("role_title", "")).strip()
        exp_html += f'<div class="entry-title">{render_spans_to_html(role_title)}</div>'

        for bullet in role.get("bullets", []) or []:
            clean_bullet = re.sub(r"^[•*\\-]\s*", "", str(bullet).strip())
            exp_html += (
                f'<div class="bullet"><span class="bullet-mark">•</span>'
                f'{render_spans_to_html(clean_bullet)}</div>'
            )

    proj_html = ""
    for proj in proj_list:
        proj_title = str(proj.get("project_title", "")).strip()
        proj_html += f'<div class="entry-title">{_project_title_html(proj_title)}</div>'

        for bullet in proj.get("bullets", []) or []:
            clean_bullet = re.sub(r"^[•*\\-]\s*", "", str(bullet).strip())
            proj_html += (
                f'<div class="bullet"><span class="bullet-mark">•</span>'
                f'{render_spans_to_html(clean_bullet)}</div>'
            )

    edu_html = education_html(edu_list)
    cert_html = certification_html(cert_list)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{
        box-sizing: border-box;
    }}

    html, body {{
        margin: 0;
        padding: 0;
        background: #ffffff;
    }}

    body {{
        font-family: Calibri, sans-serif;
        color: #000000;
        font-size: 9pt;
    }}

    .resume-page {{
        width: 100%;
        max-width: 210mm;
        aspect-ratio: 210 / 297;
        padding: 0.6in 1cm 1cm 1cm;
        margin: 0 auto;
        background: #ffffff;
        overflow: hidden;
    }}

    .header-name {{
        font-size: 20pt;
        font-weight: 400;
        text-align: center;
        line-height: 1;
        margin: 0;
    }}

    .header-title {{
        font-size: 10pt;
        font-weight: 700;
        text-align: center;
        line-height: 1.1;
        margin: 0;
    }}

    .header-contact {{
        font-size: 9pt;
        font-weight: 400;
        text-align: center;
        line-height: 1.1;
        margin: 0;
    }}

    .header-contact a,
    .project-link,
    a {{
        color: #000000;
        text-decoration: underline;
    }}

    .section-title {{
        font-size: 11pt;
        font-weight: 700;
        line-height: 1;
        margin-top: 4pt;
        margin-bottom: 2pt;
        color: #000000;
        text-transform: uppercase;
        text-decoration: underline;
    }}

    .body-text {{
        font-size: 9pt;
        line-height: 1.15;
        margin: 0;
        color: #000000;
    }}

    .skill-line {{
        font-size: 9pt;
        line-height: 1.15;
        margin: 0;
        color: #000000;
    }}

    .entry-title {{
        font-size: 10pt;
        line-height: 1.1;
        font-weight: 700;
        margin: 1pt 0 0 0;
        color: #000000;
    }}

    .bullet {{
        font-size: 9pt;
        line-height: 1.15;
        margin: 0;
        padding-left: 12px;
        text-indent: 0;
        color: #000000;
    }}

    .bullet-mark {{
        display: inline-block;
        width: 9px;
        margin-left: -12px;
        margin-right: 3px;
    }}

    .project-link {{
        font-size: 9pt;
        font-weight: 400;
    }}

    strong {{
        font-weight: 700;
    }}
</style>
</head>
<body>
<div class="resume-page">

    <div class="header-name">{html.escape(cand_name)}</div>
    <div class="header-title">Data Analyst</div>
    <div class="header-contact">{_contact_html(cand_details)}</div>

    <div class="section-title">PROFESSIONAL SUMMARY</div>
    <div class="body-text">{render_summary_with_keywords_html(summary, keywords)}</div>

    <div class="section-title">EXPERIENCE</div>
    {exp_html}

    <div class="section-title">PROJECTS</div>
    {proj_html}

    <div class="section-title">SKILLS</div>
    {skills_html}

    <div class="section-title">EDUCATION</div>
    {edu_html}

    <div class="section-title">CERTIFICATIONS</div>
    {cert_html}

</div>
</body>
</html>
"""



def _set_document_defaults(doc):
    """Set A4 page, margins and Normal style to the reference resume."""
    section = doc.sections[0]

    section.page_width = Inches(PAGE_WIDTH_IN)
    section.page_height = Inches(PAGE_HEIGHT_IN)

    section.top_margin = Inches(TOP_MARGIN_IN)
    section.bottom_margin = Inches(BOTTOM_MARGIN_IN)
    section.left_margin = Inches(SIDE_MARGIN_IN)
    section.right_margin = Inches(SIDE_MARGIN_IN)

    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = Pt(BODY_SIZE)

    # Ensure Word uses Calibri for all scripts.
    rPr = normal.element.rPr
    rFonts = rPr.rFonts
    rFonts.set(qn("w:ascii"), FONT_NAME)
    rFonts.set(qn("w:hAnsi"), FONT_NAME)
    rFonts.set(qn("w:eastAsia"), FONT_NAME)
    rFonts.set(qn("w:cs"), FONT_NAME)


def generate_new_formatted_docx(results):
    """
    Generate the downloadable optimized resume.

    The layout intentionally mirrors generate_paper_sheet_tailored_html():
    A4, Calibri, black text, same font sizes, same margins and compact
    spacing.
    """
    output = BytesIO()
    doc = docx.Document()

    _set_document_defaults(doc)

    sec2 = results.get("section_2_tailored_content", {}) or {}
    contact = sec2.get("contact_info", {}) or {}

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(0)
    p_name.paragraph_format.line_spacing = 1.0

    add_docx_run(
        p_name,
        contact.get("name", "Rohini Tembhurnikar"),
        size=NAME_SIZE,
    )

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(0)
    p_title.paragraph_format.line_spacing = 1.0

    add_docx_run(
        p_title,
        "Data Analyst",
        size=TITLE_SIZE,
        bold=True,
    )

    add_contact_line_docx(
        doc,
        contact.get(
            "details",
            "(+91) 8010132326 | rohinitembhurnikar3@gmail.com | "
            "Hyderabad, India | LinkedIn | GitHub | Portfolio | Tableau",
        ),
    )

    # --------------------------------------------------------
    # PROFESSIONAL SUMMARY
    # --------------------------------------------------------
    add_section_header_docx(doc, "PROFESSIONAL SUMMARY")

    p_summary = doc.add_paragraph()
    p_summary.paragraph_format.space_before = Pt(0)
    p_summary.paragraph_format.space_after = Pt(0)
    p_summary.paragraph_format.line_spacing = 1.15

    add_summary_with_keywords_docx(
        p_summary,
        sec2.get("professional_summary", ""),
        results.get("post_optimization", {}).get("matching_keywords", []) or [],
    )

    # --------------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------------
    add_section_header_docx(doc, "EXPERIENCE")

    for role in sec2.get("professional_experience", []) or []:
        p_role = doc.add_paragraph()
        p_role.paragraph_format.space_before = Pt(2)
        p_role.paragraph_format.space_after = Pt(0)
        p_role.paragraph_format.line_spacing = 1.0
        p_role.paragraph_format.keep_with_next = True

        add_docx_run(
            p_role,
            str(role.get("role_title", "Role")).strip(),
            size=ENTRY_TITLE_SIZE,
            bold=True,
        )

        for bullet in role.get("bullets", []) or []:
            add_resume_bullet_docx(doc, bullet)

    # --------------------------------------------------------
    # PROJECTS
    # --------------------------------------------------------
    add_section_header_docx(doc, "PROJECTS")

    for proj in sec2.get("projects", []) or []:
        _project_title_docx(
            doc,
            proj.get("project_title", "Project"),
        )

        for bullet in proj.get("bullets", []) or []:
            add_resume_bullet_docx(doc, bullet)

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------
    add_section_header_docx(doc, "SKILLS")

    for cat, val in (sec2.get("core_competencies_grouped", {}) or {}).items():
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15

        add_docx_run(p, f"{cat}: ", size=BODY_SIZE, bold=True)
        add_docx_run(p, str(val), size=BODY_SIZE)

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------
    add_section_header_docx(doc, "EDUCATION")

    for edu in sec2.get("education", []) or []:
        add_title_details_docx(doc, edu)

    # --------------------------------------------------------
    # CERTIFICATIONS
    # --------------------------------------------------------
    add_section_header_docx(doc, "CERTIFICATIONS")

    for cert in sec2.get("certifications", []) or []:
        add_title_details_docx(doc, cert)

    doc.save(output)
    output.seek(0)
    return output
