from pathlib import Path

from pdf_to_markdown_llm.config import cfg
from pdf_to_markdown_llm.service.pdf_to_text import encode_file, PROMPT_CONVERSION

import google.generativeai as genai

EXTRA_PROMPT = """

Please do not summarize the text, but instead convert the whole document to markdown.
"""


def convert_single_pdf(pdf_file: Path) -> Path:
    assert pdf_file.exists(), f"Path {pdf_file} does not exist."
    extension = pdf_file.suffix
    assert (
        extension.lower() == ".pdf"
    ), f"File {pdf_file.name} does not seem to be a file."
    model = genai.GenerativeModel(cfg.gemini_model)
    encoded_data = encode_file(pdf_file)
    response = model.generate_content(
        [
            {"mime_type": "application/pdf", "data": encoded_data},
            f"""{PROMPT_CONVERSION}{EXTRA_PROMPT}""",
        ]
    )
    md_file = pdf_file.parent / f"{pdf_file.stem}.md"
    md_file.write_text(response.text, encoding="utf-8")
    return md_file
