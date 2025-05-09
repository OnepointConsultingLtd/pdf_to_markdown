import base64
from pathlib import Path
from typing import Iterator, Callable, Awaitable

from PIL import Image

from pdf_to_markdown_llm.logger import logger
from pdf_to_markdown_llm.model.conversion import SupportedFormat, ConversionInput
from pdf_to_markdown_llm.model.process_results import ProcessResult
from pdf_to_markdown_llm.model.conversion import conversion_input_from_file

ConversionFunction = Callable[[ConversionInput], Awaitable[ProcessResult]]


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


async def convert_all_recursively(
    folders: list[Path | str],
    convert_single_file: callable,
    delete_previous: bool = False,
    extensions: list[str] = [".pdf"],
) -> list[ProcessResult]:
    process_results = []
    for path in process_folders(folders):
        if delete_previous:
            remove_expressions = ["**/*.txt", "**/*.jpg", "**/*.md", "**/*.html"]
            for expression in remove_expressions:
                for txt_file in path.rglob(expression):
                    txt_file.unlink()
        files = [file for file in path.rglob("*") if file.suffix.lower() in extensions]
        for file in files:
            logger.info(f"Started processing {file}")
            process_result = await convert_single_file(file, SupportedFormat.MARKDOWN)
            process_results.append(process_result)
            logger.info(f"Finished processing {file}")
    return process_results


async def convert_single_file(
    file: Path,
    format: SupportedFormat,
    convert_single_file: ConversionFunction,
    convert_word_to_markdown: ConversionFunction,
) -> ProcessResult:
    assert file.exists(), f"Path {file} does not exist."
    conversion_input = conversion_input_from_file(file, format)
    extension = file.suffix.lower()
    match extension:
        case ".pdf":
            return await convert_single_file(conversion_input)
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
