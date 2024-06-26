import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_hammer_core.util.message_factory import reply_text

from .codelogger import codelogger

regex_str = r"^(rs|rust|sh|bash|py|python|c|cc|cpp|c\+\+)[ \t]*\r?\n((?:.|\s)*?)$";
python_catcher = on_regex(regex_str)


@python_catcher.handle()
async def _(bot: Bot, event: Event):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', None)
    # user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    raw_msg = str(event.get_message())

    codelogger.info("get message\n" + event.get_log_string())
    regexplist: list[str] = re.findall(regex_str, raw_msg)[0]
    language: str = regexplist[0]
    content: str = regexplist[1]
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')

    if language in ["python", "py"]:
        from .pyrun import run_content_in_docker
    elif language in ["c++", "cpp", "cc", "c"]:
        from .cpprun import run_content_in_docker
    elif language in ["bash", "sh"]:
        from .shrun import run_content_in_docker
    elif language in ["rust", "rs"]:
        from .rustrun import run_content_in_docker

    res = run_content_in_docker(content)
    
    if res is not None and res != '':
        if len(res) + len(content) < 4500: # 4558:
            codelogger.info("send message\n" + res)
            await python_catcher.send(reply_text(res, event))
        else:
            codelogger.info("send message\n" + 'TooMuch')
            await python_catcher.send(reply_text("输出太多了！", event))
    else:
        codelogger.info("send message\n" + 'None')
        await python_catcher.send(reply_text("没有输出哦", event))

    await python_catcher.finish()
