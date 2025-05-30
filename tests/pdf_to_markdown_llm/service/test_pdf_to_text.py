from pathlib import Path
import asyncio

from pdf_to_markdown_llm.model.process_results import ProcessResults
from pdf_to_markdown_llm.service.openai_pdf_to_text import (
    SupportedFormat,
    encode_file,
    process_folders,
    convert_single_file,
    convert_all_recursively,
    convert_compact_pdfs,
    zip_md_files,
    convert_word_to_markdown,
    convert_pdf_to_markdown,
    convert_file,
)
from pdf_to_markdown_llm.model.conversion import (
    conversion_input_from_file,
    RecursiveConversionInput,
)
from pdf_to_markdown_llm.service.cleanup import clean_dir


def test_encode_image():
    image_file = Path(__file__) / "../../../../images/cat.jpg"
    assert image_file.exists(), f"Cannot find {image_file}"
    encoded = encode_file(image_file)
    assert encoded is not None, "Encoded is none"
    assert len(encoded) > 0, "Encoded string should not be empty"


def test_process_folders():
    base_folder = Path(__file__) / "../../../.."
    found = False
    for file in process_folders([base_folder.absolute().as_posix()]):
        found = file is not None
    assert found, "Could not find 'images' folder"


def test_convert_simple_pdf():
    pdf = Path(__file__) / "../../../../pdfs/simple/OTT Webinar 6 - AI Agents.pdf"
    assert pdf.exists(), "Cannot find the PDF file."
    result = asyncio.run(
        convert_single_file(
            pdf,
            SupportedFormat.MARKDOWN,
            convert_pdf_to_markdown,
            convert_word_to_markdown,
        )
    )
    assert result is not None, "There should be a result"
    assert len(result.exceptions) == 0, f"There are exceptions: {result.exceptions}"


def test_convert_simple_pdf_html():
    pdf = Path(__file__) / "../../../../pdfs/simple/OTT Webinar 6 - AI Agents.pdf"
    assert pdf.exists(), "Cannot find the PDF file."
    result = asyncio.run(
        convert_single_file(
            pdf, SupportedFormat.HTML, convert_pdf_to_markdown, convert_word_to_markdown
        )
    )
    assert result is not None, "There should be a result"
    assert len(result.exceptions) == 0, f"There are exceptions: {result.exceptions}"


def test_convert_single_file():
    pdf = Path(__file__) / "../../../../pdfs/oecd/002b3a39-en.pdf"
    assert pdf.exists(), "Cannot find the PDF file."
    result = asyncio.run(
        convert_single_file(
            pdf, SupportedFormat.HTML, convert_pdf_to_markdown, convert_word_to_markdown
        )
    )
    assert result is not None, "There should be a result"
    assert len(result.paths), "There are no result paths"


def test_convert_all_pdfs():
    # Note: these tests are very slow.
    paths = [
        Path(__file__) / "../../../../pdfs/oecd",
        Path(__file__) / "../../../../pdfs/who",
    ]
    assert all([p.exists() for p in paths])

    results = asyncio.run(
        convert_all_recursively(
            RecursiveConversionInput(
                folders=paths,
                convert_single_file=convert_file,
                delete_previous=False,
                extensions=[".pdf"],
            )
        )
    )
    assert len(results) == 3
    clean_dir(Path(__file__) / "../../../../pdfs")


def test_convert_compact_pdfs():
    paths = [Path(__file__) / "../../../../pdfs/oecd"]
    process_results: ProcessResults = asyncio.run(convert_compact_pdfs(paths, False))
    assert process_results is not None
    assert process_results.process_result_list is not None
    assert process_results.files_dict is not None
    assert len(process_results.process_result_list) == 2
    clean_dir(Path(__file__) / "../../../../pdfs")


def test_zip_md_files():
    paths = [
        Path(__file__) / "../../../../pdfs/oecd",
        Path(__file__) / "../../../../pdfs/who",
    ]
    process_results: ProcessResults = asyncio.run(convert_compact_pdfs(paths, False))
    assert process_results.files_dict is not None
    zip_files = zip_md_files(process_results.files_dict)
    assert len(zip_files) == 2
    clean_dir(Path(__file__) / "../../../../pdfs")


def test_convert_word_to_markdown():
    word = Path(__file__) / "../../../../docs/sample1.docx"
    assert word.exists(), "Cannot find the Word file."
    conversion_input = conversion_input_from_file(word, SupportedFormat.MARKDOWN)
    result = asyncio.run(convert_word_to_markdown(conversion_input))
    assert result is not None, "There should be a result"
    assert len(result.paths), "There are no result paths"
    clean_dir(Path(__file__) / "../../../../pdfs")
