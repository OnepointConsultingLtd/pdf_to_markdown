from pathlib import Path
from pdf_to_markdown_llm.logger import logger


def clean_dir(dir: Path):
    if not dir.exists():
        raise FileNotFoundError(f"Directory {dir} does not exist")
    expressions = ["*.md", "*.jpg", "*.html"]
    for expression in expressions:
        for file in dir.rglob(f"**/{expression}"):
            if file.is_file():
                file.unlink()
            logger.info(f"Deleted {file}")
