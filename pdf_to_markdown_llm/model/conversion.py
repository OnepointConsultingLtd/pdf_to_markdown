from pydantic import BaseModel, Field
from pathlib import Path
from enum import StrEnum
from datetime import datetime
import re


class SupportedFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"


FILE_EXTENSION = {
    SupportedFormat.MARKDOWN: "md",
    SupportedFormat.HTML: "html",
}


class ConversionInput(BaseModel):
    file: Path = Field(description="The path to the file to convert.")
    current_date_time: str = Field(description="The current date and time.")
    new_file_name: str = Field(description="The name of the new file.")
    format: SupportedFormat = Field(description="The format to convert the file to.")


class RecursiveConversionInput(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    folders: list[Path | str] = Field(description="The folders to convert.")
    convert_single_file: callable = Field(
        description="The function to convert a single file."
    )
    delete_previous: bool = Field(description="Whether to delete the previous files.")
    extensions: list[str] = Field(description="The extensions of the files to convert.")
    sample_fraction: float = Field(
        default=1.0,
        description="The fraction of files to sample. Should be between 0 and 1.",
        ge=0.0,
        le=1.0,
    )


def conversion_input_from_file(
    file: Path, format: SupportedFormat = SupportedFormat.MARKDOWN
) -> ConversionInput:
    current_date_time = datetime.now().isoformat()
    current_date_time = re.sub(r"[:.]", "", current_date_time)
    new_file_name = convert_file_name(file)
    conversion_input = ConversionInput(
        file=file,
        current_date_time=current_date_time,
        new_file_name=new_file_name,
        format=format,
    )
    return conversion_input


def convert_file_name(file: Path) -> str:
    return re.sub(r"\s+", "_", file.stem)