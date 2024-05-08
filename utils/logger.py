import logging.config
import os
from datetime import date

if not os.path.isdir("logs"):
    os.mkdir("logs")

get_current_date = date.today()
log_file_path = "logs/" + str(get_current_date)+ '.log'

def logger():
    """
    Creates a rotating log
    """
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
                "datefmt": "%d/%m/%Y %H:%M:%S",
            },
        },
        "handlers": {
            "RotatingFileHandler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "filename": log_file_path,
                "backupCount": 10,
            },
        },
        "loggers": {
            "": {
                "handlers": ["RotatingFileHandler"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)
    logging.captureWarnings(True)
    return logging
