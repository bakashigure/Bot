import re
import datetime
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

from .capture_context import get_random

reg = "^(?:#今日翻译)[:：，,\s]*([\S]*)[\s]*$"
your_plugin_catcher = on_regex(reg)

today_dict = {}

@your_plugin_catcher.handle()
async def _(bot: Bot, event: Event):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', None)
    # user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    raw_msg = str(event.get_message())

    content_list = re.findall(reg, raw_msg)
    content = content_list[0].strip().lower()

    def recog(i: str) -> str:
        s = {
            "english": "en",
            "英文": "en",
            "英语": "en",
            "jp": "ja",
            "日文": "ja",
            "日语": "ja",
            "japanese": "ja"
        }
        if i in s:
            return s[i]
        return i

    content = recog(content)
    lan = ["en", "ja"]
    if content not in lan:
        await your_plugin_catcher.send("语种暂不支持")
        await your_plugin_catcher.finish()

    today = datetime.date.today()
    today_dict.setdefault(content, (0, ""))
    if today_dict[content][0] != today or today_dict[content][1] == "":
        today_dict[content] = (today, get_random("./src/plugins/dataset/context/" + content + ".txt"))
    res = today_dict[content][1]

    if res == "":
        await your_plugin_catcher.send("翻译句库已空，请联系管理员")
    else:
        await your_plugin_catcher.send(f"翻译文本练习\n{res}")
    await your_plugin_catcher.finish()
