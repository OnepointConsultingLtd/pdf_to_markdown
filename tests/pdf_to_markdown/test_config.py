from pdf_to_markdown.config import cfg


def test_cfg():
    assert len(cfg.openai_api_key) > 0, "The model api key is empty"
    assert len(cfg.openai_model) > 0, "The model should not be empty"
    assert cfg.max_retries is not None, "Maximum retries needs to be not none"
