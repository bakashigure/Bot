# import nonebot
import re
import asyncio
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot import get_driver, on_regex
from nonebot.typing import T_State
from nonebot.params import T_State

from .data_source import get_abv_data
from .config import Config

global_config = get_driver().config
config = global_config.dict()
# b_sleep_time = config.get('b_sleep_time', 2)
# b_sleep_time = int(b_sleep_time)

# Export something for other plugin
# export = nonebot.export()
# export.foo = "bar"

# @export.xxx
# def some_function():
#     pass
biliav = on_regex("[Aa][Vv]\d{1,12}|[Bb][Vv]1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2}|[Bb]23\.[Tt][Vv]/[A-Za-z0-9]{7}")


@biliav.handle()
async def handle(bot: Bot, event: Event, state: T_State):
    abvcode_list: list[str] = re.compile(
        "[Aa][Vv]\d{1,12}|[Bb][Vv]1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2}|[Bb]23\.[Tt][Vv]/[A-Za-z0-9]{7}").findall(
        str(event.get_message()))
    if not abvcode_list:
        return
    logger.debug("start matching biliav")
    rj_list: list[str] = await get_abv_data(abvcode_list)
    for rj in rj_list:
        await biliav.send(rj)
    if len(rj_list) == 0:
        logger.debug("no data in biliav")
    logger.debug("stop sending biliav")
    await biliav.finish()
