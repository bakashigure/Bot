import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

gpt_catcher = on_regex(r"^gpt\r?\n((?:.|\s)*?)$")

@gpt_catcher.handle()
async def _(bot: Bot, event: Event):

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    raw_msg = event_dict['raw_message']

    content = re.findall(r"^gpt\r?\n((?:.|\s)*?)$", raw_msg)[0]
    reply = f'哈哈这是{content}'
    await gpt_catcher.send(reply)
    await gpt_catcher.finish()
