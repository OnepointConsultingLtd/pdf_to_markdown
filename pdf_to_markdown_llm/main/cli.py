from pathlib import Path
import click
import asyncio

from pdf_to_markdown_llm.service.pdf_to_text import (
    convert_single_file,
    compact_markdown_files_from_list,
    convert_compact_pdfs,
)
from pdf_to_markdown_llm.model.process_results import ProcessResults


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--files",
    "-f",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=str),
    multiple=True,
    help="Specify multiple pdf file paths.",
)
def convert_files(files: list[str]):
    for file in files:
        path = Path(file)
        if not path.exists():
            click.secho("Error: File not found!", fg="red", err=True)
        click.secho(f"Processing {path}", fg="green")
        process_result = asyncio.run(convert_single_file(path))
        markdown_path = compact_markdown_files_from_list(path, process_result.paths)
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


if __name__ == "__main__":
    cli()
