import sys
import logging

bililogger = logging.getLogger("biliav")
bililogger.setLevel(logging.DEBUG)
bililogger.propagate = False

hfh_formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
)
hfh = logging.handlers.RotatingFileHandler(
    '../biliav.log', mode="a", maxBytes=1024 * 1024 * 8, backupCount=1
)
hfh.setFormatter(hfh_formatter)
bililogger.addHandler(hfh)

hsh_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(module)s | %(message)s"
)
hsh = logging.StreamHandler(sys.stdout)
hsh.setFormatter(hsh_formatter)
bililogger.addHandler(hsh)
