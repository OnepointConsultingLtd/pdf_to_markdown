from pathlib import Path

import pytest

from pdf_to_markdown_llm.model.conversion import SupportedFormat
from pdf_to_markdown_llm.model.process_results import ProcessResult
from pdf_to_markdown_llm.service.conversion_support import convert_single_file
from pdf_to_markdown_llm.service.ollama_text_conversion import (
    convert_pdf_to_markdown,
    convert_word_to_markdown,
)
from pdf_to_markdown_llm.config import cfg


@pytest.mark.asyncio
async def test_convert_pdf_to_markdown_ollama():
    if cfg.ollama_base_url is not None and cfg.ollama_base_url.strip() == "":
        return
    pdf_file = Path(__file__) / "../../../../pdfs/oecd/002b3a39-en.pdf"
    assert pdf_file.exists(), f"Cannot find the PDF file: {pdf_file.as_posix()}"

    result: ProcessResult = await convert_single_file(
        pdf_file,
        SupportedFormat.MARKDOWN,
        convert_pdf_to_markdown,
        convert_word_to_markdown,
    )
    assert len(result.paths) > 0
    assert result.paths[0].exists()
    assert result.paths[0].suffix == ".md"
