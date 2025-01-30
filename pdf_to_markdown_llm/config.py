import os

from dotenv import load_dotenv

load_dotenv()

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


cfg = Config()
