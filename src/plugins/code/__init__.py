import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_hammer_core.util.message_factory import reply_text

from .pythonlogger import pylogger

python_catcher = on_regex(r"^(rust|sh|bash|python|cpp|c\+\+)\r?\n((?:.|\s)*?)$")


@python_catcher.handle()
async def _(bot: Bot, event: Event):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', None)
    # user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    raw_msg = str(event.get_message())

    pylogger.debug(event.get_log_string())
    regexplist: list[str] = re.findall(r"^(rust|sh|bash|python|cpp|c\+\+)\r?\n((?:.|\s)*?)$", raw_msg)[0]
    language: str = regexplist[0]
    content: str = regexplist[1]
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')

    if language in ["python"]:
        from .pyrun import run_content_in_docker
    elif language in ["c++", "cpp"]:
        from .cpprun import run_content_in_docker
    elif language in ["bash", "sh"]:
        from .shrun import run_content_in_docker
    elif language in ["rust"]:
        from .rustrun import run_content_in_docker

    res = run_content_in_docker(content)
    
    if res is not None and res != '':
        if len(res) + len(content) < 4500: # 4558:
            pylogger.info(res)
            await python_catcher.send(reply_text(res, event))
        else:
            pylogger.info('TooMuch')
            await python_catcher.send(reply_text("输出太多了！", event))
    else:
        pylogger.error('None')
        await python_catcher.send(reply_text("没有输出哦", event))
    await python_catcher.finish()
