import base64
import asyncio
import re
import zipfile
from enum import StrEnum

from datetime import datetime
from pathlib import Path
from typing import Iterator
from collections import defaultdict

from pdf2image import convert_from_path
from openai import AsyncOpenAI
from PIL import Image

from pdf_to_markdown_llm.config import cfg
from pdf_to_markdown_llm.logger import logger
from pdf_to_markdown_llm.model.process_results import ProcessResult, ProcessResults

CANNOT_CONVERT = "Cannot convert"


class SupportedFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"


FILE_EXTENSION = {
    SupportedFormat.MARKDOWN: "md",
    SupportedFormat.HTML: "html",
}


CONVERSION_PROMPTS = {
    SupportedFormat.MARKDOWN: f"""Convert this pdf into markdown following these rules:
- IGNORE HEADERS AND FOOTERS.
- if you cannot convert the image to markdown, then just convert the image to plain text
- if you cannot convert the image to plain text, write exaclty: "{CANNOT_CONVERT}" and in the line below specify the reason.
    """,
    SupportedFormat.HTML: f"""Convert this pdf into html following these rules:
- IGNORE HEADERS AND FOOTERS.
- if you cannot convert the image to html, then just convert the image to plain text
- if you cannot convert the image to plain text, write exaclty: "{CANNOT_CONVERT}" and in the line below specify the reason.
- Do not add <head> or <body> elements, just generate the html that you otherwise would include in an existing <body> element.
    """,
}

openai_client = AsyncOpenAI()


def encode_file(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def convert_single_file(
    file: Path, format: SupportedFormat = SupportedFormat.MARKDOWN
) -> ProcessResult:
    assert file.exists(), f"Path {file} does not exist."
    current_date_time = datetime.now().isoformat()
    current_date_time = re.sub(r"[:.]", "", current_date_time)
    new_file_name = re.sub(r"\s+", "_", file.stem)
    return await convert_pdf_to_markdown(file, current_date_time, new_file_name, format)


def process_folders(folders: list[str]) -> Iterator[Path]:
    for arg in folders:
        path = Path(arg)
        if path.exists():
            yield path
        else:
            logger.error(f"{path} does not exist.")


async def convert_all_pdfs(
    folders: list[Path | str], delete_previous: bool = False
) -> list[ProcessResult]:
    process_results = []
    for path in process_folders(folders):
        if delete_previous:
            remove_expressions = ["**/*.txt", "**/*.jpg", "**/*.md", "**/*.html"]
            for expression in remove_expressions:
                for txt_file in path.rglob(expression):
                    txt_file.unlink()
        pdf_files = [file for file in path.rglob("*") if file.suffix.lower() == ".pdf"]
        for pdf in pdf_files:
            logger.info(f"Started processing {pdf}")
            process_result = await convert_single_file(pdf)
            process_results.append(process_result)
            logger.info(f"Finished processing {pdf}")
    return process_results


async def convert_compact_pdfs(
    folders: list[Path | str], delete_previous: bool = False
) -> ProcessResults:
    process_result_list = await convert_all_pdfs(folders, delete_previous)
    files_dict = await compact_files(folders)
    return ProcessResults(
        process_result_list=process_result_list, files_dict=files_dict
    )


async def convert_pdf_to_markdown(
    file: Path, current_date_time: int, new_file_name: str, format: SupportedFormat
) -> ProcessResult:
    process_result = ProcessResult([], [])
    try:
        pages = convert_from_path(file)
        batches = [
            pages[i : i + cfg.batch_size] for i in range(0, len(pages), cfg.batch_size)
        ]

        for i, batch in enumerate(batches):
            asynch_batch = [
                __process_page(
                    file,
                    current_date_time,
                    new_file_name,
                    j + cfg.batch_size * i,
                    page,
                    format,
                )
                for j, page in enumerate(batch)
            ]
            results: list[ProcessResult] = await asyncio.gather(*asynch_batch)
            for pr in results:
                process_result.exceptions.extend(pr.exceptions)
                process_result.paths.extend(pr.paths)
    except Exception as e:
        logger.exception(f"Cannot process {file}")
        process_result.exceptions.append(e)
    return process_result


async def __process_page(
    file: Path,
    current_date_time: str,
    new_file_name: str,
    i: int,
    page: Image.Image,
    format: SupportedFormat,
) -> ProcessResult:
    logger.info(f"Format: {format}.")
    success = False
    retry_count = 0
    process_result = ProcessResult([], [])
    while not success and retry_count < cfg.max_retries:
        try:
            page_file = file.parent / f"{new_file_name}_{current_date_time}_{i+1}.jpg"
            logger.info(f"Processing {page_file}")
            page.save(page_file, "JPEG")
            image_data = encode_file(page_file)
            file_extension = FILE_EXTENSION[format]
            new_file = file.parent / f"{new_file_name}_{i+1}.{file_extension}"
            new_file = new_file.resolve()
            if not new_file.exists():
                messages = __build_messages(image_data, format)
                response = await openai_client.chat.completions.create(
                    model=cfg.openai_model, messages=messages
                )
                markdown = response.choices[0].message.content
                new_file.write_text(markdown, encoding="utf-8")
            else:
                logger.warning(f"File {new_file} already exists.")
            process_result.paths.append(new_file)
            success = True
        except Exception as e:
            logger.exception("Failed to process image.")
            retry_count += 1
            process_result.exceptions.append(e)
    return process_result


def __build_messages(image_data: str, format: SupportedFormat):

    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are a powerful AI system that can convert PDFs to markdown.",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": CONVERSION_PROMPTS[format],
                },
                {
                    "type": "text",
                    "text": "use your built-in gpt-4 machine vision to extract and describe the text contents of my attached picture",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}",
                    },
                },
            ],
        },
    ]
    return messages


async def compact_files(
    folders: list[str], format: SupportedFormat
) -> dict[Path, list[Path]]:
    all_aggregate_files = {}
    for path in process_folders(folders):
        file_extension = FILE_EXTENSION[format]
        previous_files = path.rglob(f"**/*_aggregate.{file_extension}")
        for pf in previous_files:
            pf.unlink()  # Delete previous files
        files = path.rglob(f"**/*{file_extension}")
        aggregate_dict = defaultdict(list)
        for file in files:
            if "_aggregate" not in file.name and re.match(
                r".+\d+\." + file_extension, file.name
            ):
                key = re.sub(r"(.+)\_\d+\." + file_extension, r"\1", file.name)
                aggregate_dict[
                    file.parent / f"{key}_aggregate." + file_extension
                ].append(file)
        all_aggregate_files[path] = compact_markdown_files(aggregate_dict, format)
    return all_aggregate_files


def compact_markdown_files(
    aggregate_dict: dict[Path, list[Path]],
    format: SupportedFormat = SupportedFormat.MARKDOWN,
) -> list[Path]:
    aggregate_files = []
    for target_file, pages in aggregate_dict.items():
        with open(target_file, "wt", encoding="utf-8") as f:
            for page in pages:
                content = page.read_text(encoding="utf-8")
                if CANNOT_CONVERT not in content:
                    f.write(content)
            f.write("\n")
        remove_markdown_tags(target_file, True, format)
        logger.info(f"Finished {target_file}")
        aggregate_files.append(target_file)
    return aggregate_files


def compact_markdown_files_from_list(
    markdown_file: Path,
    paths: list[Path],
    format: SupportedFormat = SupportedFormat.MARKDOWN,
) -> Path | None:
    target_file = (
        markdown_file.parent / f"{markdown_file.stem}.{FILE_EXTENSION[format]}"
    )
    aggregate_dict = {target_file: paths}
    file_list = compact_markdown_files(aggregate_dict, format)
    if len(file_list):
        return file_list[0]
    return None


def remove_markdown_tags(
    markdown_file: Path,
    override: bool = False,
    format: SupportedFormat = SupportedFormat.MARKDOWN,
):
    output = []
    markdown_start = f"```{format}"
    with open(markdown_file, "r", encoding="utf-8") as f:
        for line in f:
            if markdown_start in line:
                output.append(line.replace(markdown_start, ""))
            elif line.startswith("```"):
                output.append(line.replace("```", ""))
            else:
                output.append(line)
    clean = "".join(output)
    if override:
        markdown_file.write_text(clean, encoding="utf-8")
    return clean


def zip_md_files(files_dict: dict[Path, list[Path]]) -> list[Path]:
    zipped_files = []
    for folder, files in files_dict.items():
        output_zip = folder.parent / f"{folder.name}.zip"
        with zipfile.ZipFile(
            output_zip,
            "w",
            zipfile.ZIP_LZMA if len(files) > cfg.lzma_limit else zipfile.ZIP_DEFLATED,
        ) as zipf:
            for file in files:
                zipf.write(file, arcname=file.relative_to(folder.parent))
        zipped_files.append(output_zip)
    return zipped_files
