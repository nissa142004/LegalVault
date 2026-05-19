from pathlib import Path

from docx import Document
from PyPDF2 import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text(file_path: str | Path) -> str:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(path)
    if extension == ".docx":
        return extract_docx_text(path)

    raise ValueError("Only PDF and DOCX files are supported.")


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]

    return "\n".join(pages).strip()


def extract_docx_text(file_path: Path) -> str:
    document = Document(str(file_path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]

    return "\n".join(paragraphs).strip()
