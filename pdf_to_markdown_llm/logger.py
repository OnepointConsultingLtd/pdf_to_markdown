from pathlib import Path

import logging
import logging.config
import yaml

with open(Path(__file__)/"../../logging_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger("pdf_to_markdown")
