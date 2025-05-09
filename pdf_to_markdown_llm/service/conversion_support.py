import base64
from pathlib import Path
from typing import Iterator

from PIL import Image

from pdf_to_markdown_llm.logger import logger
from pdf_to_markdown_llm.model.conversion import SupportedFormat
from pdf_to_markdown_llm.model.process_results import ProcessResult
from pdf_to_markdown_llm.model.conversion import conversion_input_from_file


def encode_file(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def process_folders(folders: list[str]) -> Iterator[Path]:
    for arg in folders:
        path = Path(arg)
        if path.exists():
            yield path
        else:
            logger.error(f"{path} does not exist.")


async def convert_single_file(
    file: Path,
    format: SupportedFormat,
    convert_pdf_to_markdown: callable,
    convert_word_to_markdown: callable,
) -> ProcessResult:
    assert file.exists(), f"Path {file} does not exist."
    conversion_input = conversion_input_from_file(file, format)
    extension = file.suffix.lower()
    match extension:
        case ".pdf":
            return await convert_pdf_to_markdown(conversion_input)
        case ".docx":
            return await convert_word_to_markdown(conversion_input)
        case _:
            raise ValueError(f"Unsupported file extension: {extension}")
        

def convert_image_to_file(page: Image.Image, page_file: Path) -> Path:
    logger.info(f"Processing {page_file}")
    if page.mode in ("RGBA", "LA"):
        page = page.convert("RGB")
    page.save(page_file, "JPEG")
    return page_file
