from pathlib import Path

import pytest

from pdf_to_markdown_llm.model.conversion import (
    SupportedFormat,
    RecursiveConversionInput,
)
from pdf_to_markdown_llm.model.conversion import conversion_input_from_file
from pdf_to_markdown_llm.service.docling_text_conversion import (
    convert_document_to_markdown,
    convert_single_file,
    convert_folders,
)
from pdf_to_markdown_llm.config import cfg
from pdf_to_markdown_llm.service.cleanup import clean_dir


@pytest.mark.asyncio
async def test_convert_pdf_to_markdown():
    pdf_file = Path(__file__) / "../../../../pdfs/oecd/002b3a39-en.pdf"
    assert pdf_file.exists(), f"Cannot find the PDF file: {pdf_file.as_posix()}"
    conversion_input = conversion_input_from_file(pdf_file, SupportedFormat.MARKDOWN)
    final_path = convert_document_to_markdown(conversion_input)
    assert final_path.exists()
    assert final_path.read_text(encoding="utf-8") != ""


@pytest.mark.asyncio
async def test_convert_folders():
    pdf_folder = Path(__file__) / "../../../../pdfs/oecd"
    doc_folder = Path(__file__) / "../../../../docs/sample"
    assert pdf_folder.exists()
    assert pdf_folder.is_dir()
    assert doc_folder.exists()
    assert doc_folder.is_dir()
    input = RecursiveConversionInput(
        folders=[pdf_folder, doc_folder],
        convert_single_file=convert_single_file,
        delete_previous=True,
        extensions=[".pdf", ".docx"],
    )
    results = await convert_folders(input)
    assert len(results) == 3
    assert results[0].exists()
    assert results[1].exists()
    clean_dir(pdf_folder)
    clean_dir(doc_folder)
