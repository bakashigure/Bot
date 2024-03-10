import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

from .pythonlogger import pylogger
from .pyrun import run_content_in_docker

python_catcher = on_regex(r"^(?:python\r?\n)((?:.|\s)*?)$")


@python_catcher.handle()
async def _(bot: Bot, event: Event):

    raw_msg = str(event.get_message())
    pylogger.debug(event.get_log_string())
    content: str = re.findall(r"^(?:python\r?\n)((?:.|\s)*?)$", raw_msg)[0]
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')

    res = run_content_in_docker(content)

    if res is not None and res != '':
        pylogger.info(res)
        await python_catcher.send(res)
    else:
        pylogger.error('None')
    await python_catcher.finish()
