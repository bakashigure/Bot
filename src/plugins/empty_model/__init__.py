import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

your_plugin_catcher = on_message(rule=startswith(("开头内容 第一种用以测试一般不会触发#$%", "开头内容 第二种用以测试一般不会触发#$%")))
# your_plugin_catcher = on_regex("^(?:开头内容)[:：，,\s]*(-?[\S]*)[:：，,\s]*(-?[\S]*)[\s]*$")

@your_plugin_catcher.handle()
async def _(bot: Bot, event: Event):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', None)
    # user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    raw_msg = str(event.get_message())

    content = re.findall('^(?:开头内容)[:：，,\s]*(-?[\S]*)[:：，,\s]*(-?[\S]*)[\s]*$', raw_msg)
    reply = f'哈哈这是{content}'
    await your_plugin_catcher.send(reply)
    await your_plugin_catcher.finish()
