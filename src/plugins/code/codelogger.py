import sys
import logging

codelogger = logging.getLogger("codelogger")
codelogger.setLevel(logging.DEBUG)
codelogger.propagate = False

hfh_formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
)
hfh = logging.handlers.RotatingFileHandler(
    '../codelogger.log', mode="a", maxBytes=1024 * 1024 * 8, backupCount=1
)
hfh.setFormatter(hfh_formatter)
codelogger.addHandler(hfh)

