import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_hammer_core.util.message_factory import reply_text

from .pythonlogger import pylogger

python_catcher = on_regex(r"^(sh|bash|python|cpp|c\+\+)\r?\n((?:.|\s)*?)$")


@python_catcher.handle()
async def _(bot: Bot, event: Event):

    raw_msg = str(event.get_message())
    pylogger.debug(event.get_log_string())
    regexplist: list[str] = re.findall(r"^(sh|bash|python|cpp|c\+\+)\r?\n((?:.|\s)*?)$", raw_msg)[0]
    language: str = regexplist[0]
    content: str = regexplist[1]
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')

    if language == "python":
        from .pyrun import run_content_in_docker
    elif language in ["c++", "cpp"]:
        from .cpprun import run_content_in_docker
    elif language in ["bash", "sh"]:
        from .shrun import run_content_in_docker

    res = run_content_in_docker(content)
    
    if res is not None and res != '':
        pylogger.info(res)
        await python_catcher.send(reply_text(res, event))
    else:
        pylogger.error('None')
        await python_catcher.send(reply_text("没有输出哦", event))
    await python_catcher.finish()
