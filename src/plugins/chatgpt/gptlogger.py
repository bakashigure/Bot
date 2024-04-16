import sys
import logging

gptlogger = logging.getLogger("gpt")
gptlogger.setLevel(logging.DEBUG)
gptlogger.propagate = False

hfh_formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
)
hfh = logging.handlers.RotatingFileHandler(
    '../gpt.log', mode="a", maxBytes=1024 * 1024 * 8, backupCount=1
)
hfh.setFormatter(hfh_formatter)
gptlogger.addHandler(hfh)

hsh_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(module)s | %(message)s"
)
hsh = logging.StreamHandler(sys.stdout)
hsh.setFormatter(hsh_formatter)
gptlogger.addHandler(hsh)
