from pathlib import Path

from pdf_to_markdown_llm.config import cfg
from pdf_to_markdown_llm.service.pdf_to_text import encode_file, PROMPT_CONVERSION

import google.generativeai as genai


def convert_single_pdf(pdf_file: Path) -> Path:
    assert pdf_file.exists(), f"Path {pdf_file} does not exist."
    extension = pdf_file.suffix
    assert extension.lower() == ".pdf", f"File {pdf_file.name} does not seem to be a file."
    model = genai.GenerativeModel(cfg.gemini_model)
    encoded_data = encode_file(pdf_file)
    response = model.generate_content([{'mime_type': 'application/pdf', 'data': encoded_data}, PROMPT_CONVERSION])
    md_file = pdf_file.parent/f"{pdf_file.stem}.md"
    return md_file

