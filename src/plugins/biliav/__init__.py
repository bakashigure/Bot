import re
import asyncio

from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot import get_driver, on_regex
from nonebot.typing import T_State
from nonebot.params import T_State

from .bililogger import bililogger
from .data_source import get_abv_data

reg = "[Aa][Vv]\d{1,12}|[Bb][Vv]1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2}|[Bb]23\.[Tt][Vv]/[A-Za-z0-9]{7}"
biliav = on_regex(reg)

@biliav.handle()
async def handle(bot: Bot, event: Event, state: T_State):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', None)
    # user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    raw_msg = event.get_plaintext()

    abvcode_list: list[str] = re.compile(reg).findall(raw_msg)
    if not abvcode_list:
        return

    logger.debug("start matching biliav")

    bililogger.info("get message\n" + event.get_log_string())
    rj_list: list[str] = await get_abv_data(abvcode_list)
    for rj in rj_list:
        await biliav.send(rj)
    if len(rj_list) == 0:
        bililogger.warning("no data in biliav")

    logger.debug("stop sending biliav")

    await biliav.finish()
