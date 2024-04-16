import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment

import httpx
from cairosvg import svg2png
from urllib.parse import quote

latex_catcher = on_regex(r"^latex[ \t]*\r?\n((?:.|\s)*?)$")

HEADER = {                                                                                                                  "Content-Type": "application/json; charset=utf-8",                                                                      "Accept": "image/gif, image/jpeg, image/pjpeg, application/x-ms-application, application/xaml+xml, application/x-ms-xbap, */*",
    "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; Tablet PC 2.0; wbx 1.0.0; wbxapp 1.0.0; Zoom 3.6.0)"
}

@latex_catcher.handle()
async def _(bot: Bot, event: Event):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', None)
    # user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    raw_msg = str(event.get_message())
    regexplist: list[str] = re.findall(r"^latex[ \t]*\r?\n((?:.|\s)*?)$", raw_msg)[0]
    content = regexplist
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')

    url_content = quote(content)
    url = f"https://latex.codecogs.com/svg.image?{url_content}"
    logger.info(f"getting {url}")

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADER)

    svg2png(bytestring=r.text, dpi=400, write_to='tmp.png')
    await latex_catcher.send(MessageSegment.image('tmp.png'))
    await latex_catcher.finish()

