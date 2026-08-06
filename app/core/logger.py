import logging
import sys
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("app_name_here")
logger.propagate = False

log_formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)s %(message)s',
)

log_stdout_handler = logging.StreamHandler(sys.stdout)
log_stdout_handler.setFormatter(log_formatter)

log_rotating_file_handler = RotatingFileHandler(
    "logs/pdf_ingestion_service.log",
    maxBytes=1024*10,
    backupCount=5,
    # encoding="utf-8",
    # delay=False,  # if True, file is opened
    # mode='a',  # 'w' or '
)
log_rotating_file_handler.setFormatter(log_formatter)

logger.handlers = [log_stdout_handler, log_rotating_file_handler]
logger.setLevel(logging.DEBUG)

# @TODO use https://pypi.org/project/python-logging-loki-v2/ to push logs to loki
