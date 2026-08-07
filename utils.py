import docx
from pypdf import PdfReader
from io import BytesIO

def extract_text_from_file(uploaded_file):
    """Extracts text content from PDF or Word upload."""
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            text += page.extract_text() or ""
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text

def create_docx(content_str):
    """Converts text/markdown content into a downloadable DOCX file."""
    doc = docx.Document()
    for paragraph in content_str.split("\n\n"):
        doc.add_paragraph(paragraph)
    
    target = BytesIO()
    doc.save(target)
    target.seek(0)
    return target
