from pdf2image import convert_from_path

import httpx

from pdf_to_markdown_llm.model.process_results import ProcessResult
from pdf_to_markdown_llm.model.conversion import ConversionInput
from pdf_to_markdown_llm.model.conversion import SupportedFormat
from pdf_to_markdown_llm.service.conversion_support import (
    encode_file,
    convert_image_to_file,
)
from pdf_to_markdown_llm.config import cfg
from pdf_to_markdown_llm.logger import logger


def select_prompt(format: SupportedFormat, language: str = "English") -> str:
    match format:
        case SupportedFormat.MARKDOWN:
            return f"""Extract all text content from this image in {language} **exactly as it appears**, without modification, summarization, or omission.
Format the output in markdown:
    - Use headers (#, ##, ###) **only if they appear in the image**
    - Preserve original lists (-, *, numbered lists) as they are
    - Maintain all text formatting (bold, italics, underlines) exactly as seen
    - **Do not add, interpret, or restructure any content**"""
        case SupportedFormat.HTML:
            return f"""Extract all text content from this image in {language} **exactly as it appears**, without modification, summarization, or omission.
Format the output in markdown:
    - Use headers (<h1>, <h2>, <h3>, <h4>, <h5>, <h6>) **only if they appear in the image**
    - Preserve original lists (<ul>, <ol>) as they are
    - Maintain all text formatting (bold, italics, underlines) exactly as seen
    - **Do not add, interpret, or restructure any content**"""


async def convert_pdf_to_markdown(conversion_input: ConversionInput) -> ProcessResult:
    """
    Convert a PDF file to markdown using OpenAI's API.

    Args:
        file (Path): The path to the PDF file to convert.
        current_date_time (int): The current date and time.
        new_file_name (str): The name of the new file.
        format (SupportedFormat): The format to convert the PDF to.
    """
    file, current_date_time, new_file_name, format = (
        conversion_input.file,
        conversion_input.current_date_time,
        conversion_input.new_file_name,
        conversion_input.format,
    )
    process_result = ProcessResult([], [])
    try:
        pages = convert_from_path(file)
        logger.info(f"Converting {file} to {len(pages)} pages")
        for i, page in enumerate(pages):
            page_file = (
                file.parent / f"{new_file_name}_{current_date_time}_{i+1}.jpg"
            ).resolve()
            page_file = convert_image_to_file(page, page_file)
            image_base64 = encode_file(page_file)
            prompt = select_prompt(format)
            # Prepare the request payload
            payload = {
                "model": cfg.ollama_model,
                "prompt": prompt,
                "stream": False,
                "images": [image_base64],
            }
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        cfg.ollama_base_url, json=payload, timeout=600
                    )
                    response.raise_for_status()
                    res = response.json().get("response", "")
                    process_result.paths.append(
                        file.parent / f"{new_file_name}_{current_date_time}_{i+1}.md"
                    )
                    process_result.paths[-1].write_text(res)
                    logger.info(f"Extracted {file} using {cfg.ollama_model}.")
                except Exception as e:
                    logger.exception(f"Cannot process {file}: {str(e)}")
                    process_result.exceptions.append(e)

    except Exception as e:
        logger.exception(f"Cannot process {file}")


async def convert_word_to_markdown(conversion_input: ConversionInput) -> ProcessResult:
    pass
