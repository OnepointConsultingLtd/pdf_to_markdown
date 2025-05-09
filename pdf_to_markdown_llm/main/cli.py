from pathlib import Path
from enum import StrEnum
import click
import asyncio

from pdf_to_markdown_llm.service.openai_pdf_to_text import (
    SupportedFormat,
    compact_markdown_files_from_list,
    convert_compact_pdfs,
)
from pdf_to_markdown_llm.model.process_results import ProcessResults
from pdf_to_markdown_llm.service.gemini_pdf_to_text import convert_single_pdf
from pdf_to_markdown_llm.service.cleanup import clean_dir
from pdf_to_markdown_llm.service.analyze_files import analyze_file_sizes
from pdf_to_markdown_llm.service.conversion_support import convert_single_file


class Engine(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--files",
    "-f",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=str),
    multiple=True,
    help="Specify multiple pdf or docx file paths.",
)
@click.option(
    "--engine",
    "-e",
    type=click.Choice([e.value for e in Engine], case_sensitive=False),
    default=Engine.OPENAI,
    show_default=True,
    help="Convert single files using either OpenAI or Gemini (requires keys).",
)
@click.option(
    "--format",
    "-t",
    type=click.Choice(
        [format.value for format in SupportedFormat], case_sensitive=False
    ),
    multiple=False,
    default=SupportedFormat.MARKDOWN,
    help="Specify the file format",
)
def convert_files(files: list[str], engine: str, format: str):
    for file in files:
        path = Path(file)
        if not path.exists():
            click.secho("Error: File not found!", fg="red", err=True)
        click.secho(f"Processing {path}", fg="green")
        click.secho(f"Using {engine} engine.", fg="green")
        match engine:
            case Engine.OPENAI:
                process_result = asyncio.run(convert_single_file(path, format))
                markdown_path = compact_markdown_files_from_list(
                    path, process_result.paths, format
                )
            case Engine.GEMINI:
                # Only supports markdown
                markdown_path = convert_single_pdf(path)
        click.secho(f"Finished converting {path} to {markdown_path}", fg="green")


@cli.command()
@click.option(
    "--dirs",
    "-d",
    type=click.Path(exists=True, dir_okay=True, readable=True, path_type=str),
    multiple=True,
    help="Specify multiple directories",
)
def convert_in_dir(dirs: list[str]):
    process_results: ProcessResults = asyncio.run(convert_compact_pdfs(dirs, False))
    for generated_list in process_results.files_dict.values():
        for md_file in generated_list:
            click.secho(f"Generated {md_file}", fg="green")


@cli.command()
@click.option(
    "--dirs",
    "-d",
    type=click.Path(exists=True, dir_okay=True, readable=True, path_type=str),
    multiple=True,
    help="Specify multiple directories to clean",
)
def clean_dirs(dirs: list[str]):
    for dir in dirs:
        clean_dir(Path(dir))


@cli.command()
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True, dir_okay=True, readable=True, path_type=str),
    multiple=False,
    help="Specify a directory to analyze",
)
def analyze_dir(dir: str):
    analyze_file_sizes(Path(dir))


if __name__ == "__main__":
    cli()
