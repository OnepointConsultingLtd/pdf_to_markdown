from pathlib import Path
from pdf_to_markdown_llm.service.gemini_pdf_to_text import convert_single_pdf


def test_convert_single_pdf():
    pdf = Path(__file__) / "../../../../pdfs/oecd/002b3a39-en.pdf"
    assert pdf.exists(), "Cannot find the PDF file."
    md_file = convert_single_pdf(pdf)
    assert md_file is not None, "There is not markdown file."
    assert md_file.exists(), "Cannot find the markdown file."
