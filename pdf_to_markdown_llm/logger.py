import sys
from pathlib import Path

import logging
import logging.config
import yaml

log_config = (Path(__file__) / "../logging_config.yaml").resolve()
try:
    with open(log_config, "r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)
except Exception as e:
    sys.stderr.write(f"Cannot find {log_config}: {e}\n")
    default_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "WARNING",
                "stream": "ext://sys.stderr",
            }
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }
    logging.config.dictConfig(default_config)

logger = logging.getLogger("pdf_to_markdown")
