#logger.py
import logging
from logging.config import dictConfig

def setup_logger():
    logging_config = dict(
        version=1,
        formatters={
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
        },
        handlers={
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        root={
            'handlers': ['console'],
            'level': 'INFO',
        },
    )
    dictConfig(logging_config)
    return logging.getLogger(__name__)

logger = setup_logger()
