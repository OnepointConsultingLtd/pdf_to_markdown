import os

from dotenv import load_dotenv
from pdf_to_markdown_llm.logger import logger

load_dotenv(".env")


class Config:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    assert (
        openai_api_key is not None
    ), "Please specify the OPENAI_API_KEY environment variable"

    openai_model = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")
    assert len(openai_model) > 0, "Open AI model should not be empty"

    batch_size = int(os.getenv("BATCH_SIZE", "5"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    lzma_limit = int(os.getenv("LZMA_LIMIT", "10"))

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    assert gemini_api_key is not None and len(
        gemini_api_key
    ), "Please specify the Gemini key."
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    ollama_base_url = os.getenv(
        "OLLAMA_BASE_URL", "http://localhost:11434/api/generate"
    )
    if not ollama_base_url or ollama_base_url.strip() == "":
        logger.warning("OLLAMA_BASE_URL is not set, using default value")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision:11b")


cfg = Config()
