from pathlib import Path

from docling.document_converter import DocumentConverter
from pdf_to_markdown_llm.model.conversion import (
    ConversionInput,
    SupportedFormat,
    RecursiveConversionInput,
)
from pdf_to_markdown_llm.model.conversion import conversion_input_from_file
from pdf_to_markdown_llm.service.conversion_support import convert_all_recursively


def convert_document_to_markdown(conversion_input: ConversionInput) -> Path:
    converter = DocumentConverter()
    result = converter.convert(conversion_input.file)
    extension = "md"
    match conversion_input.format:
        case SupportedFormat.MARKDOWN:
            text = result.document.export_to_markdown()
        case SupportedFormat.HTML:
            text = result.document.export_to_html()
            extension = "html"
        case _:
            raise ValueError(f"Unsupported format: {conversion_input.format}")
    new_file = (
        conversion_input.file.parent / f"{conversion_input.new_file_name}.{extension}"
    )
    new_file.write_text(text, encoding="utf-8")
    return new_file


async def convert_single_file(file: Path, format: SupportedFormat) -> Path:
    conversion_input = conversion_input_from_file(file, format)
    return convert_document_to_markdown(conversion_input)


async def convert_folders(
    recursive_conversion_input: RecursiveConversionInput,
) -> list[Path]:
    return await convert_all_recursively(recursive_conversion_input)
