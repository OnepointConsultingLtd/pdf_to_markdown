import base64
import random
import zipfile

from pathlib import Path
from typing import Iterator, Callable, Awaitable

from PIL import Image

from pdf_to_markdown_llm.logger import logger
from pdf_to_markdown_llm.model.conversion import (
    SupportedFormat,
    ConversionInput,
    RecursiveConversionInput,
)
from pdf_to_markdown_llm.model.process_results import ProcessResult
from pdf_to_markdown_llm.model.conversion import conversion_input_from_file, convert_file_name
from pdf_to_markdown_llm.config import cfg


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
    recursive_conversion_input: RecursiveConversionInput,
) -> list[ProcessResult]:
    process_results = []
    for path in process_folders(recursive_conversion_input.folders):
        if recursive_conversion_input.delete_previous:
            remove_expressions = ["**/*.txt", "**/*.jpg", "**/*.md", "**/*.html"]
            for expression in remove_expressions:
                for txt_file in path.rglob(expression):
                    txt_file.unlink()
        files = [
            file
            for file in path.rglob("*")
            if file.suffix.lower() in recursive_conversion_input.extensions
        ]
        total_files = len(files)
        for i, file in enumerate(files):
            if (
                recursive_conversion_input.sample_fraction == 1.0
                or random.uniform(0, 1) < recursive_conversion_input.sample_fraction
            ):
                try:
                    logger.info(f"Started processing {file} ({i+1}/{total_files})")
                    if (file.parent / f"{file.stem}.md").exists() or (file.parent / f"{convert_file_name(file)}.md").exists():
                        logger.info(f"Skipping {file} because it already exists.")
                        continue
                    process_result = (
                        await recursive_conversion_input.convert_single_file(
                            file, SupportedFormat.MARKDOWN
                        )
                    )
                    process_results.append(process_result)
                    logger.info(f"Finished processing {file}")
                except Exception as e:
                    logger.error(f"Error processing {file}: {e}")
            else:
                logger.info(f"Skipping {file} because it is not in the sample.")
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


def compress_recursive(path: Path):
    output_zip = path.parent / f"{path.name}.zip"
    files = list(path.rglob("**/*.md")) + list(path.rglob("**/*.txt"))
    with zipfile.ZipFile(
        output_zip,
        "w",
        zipfile.ZIP_LZMA if len(files) > cfg.lzma_limit else zipfile.ZIP_DEFLATED,
    ) as zipf:
        for file in files:
            if file.is_file():
                zipf.write(file, arcname=file.relative_to(path.parent))
    return output_zip
