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


def conversion_input_from_file(file: Path, format: SupportedFormat = SupportedFormat.MARKDOWN) -> ConversionInput:
    current_date_time = datetime.now().isoformat()
    current_date_time = re.sub(r"[:.]", "", current_date_time)
    new_file_name = re.sub(r"\s+", "_", file.stem)
    conversion_input = ConversionInput(file=file, 
                                       current_date_time=current_date_time, 
                                       new_file_name=new_file_name, 
                                       format=format)
    return conversion_input

