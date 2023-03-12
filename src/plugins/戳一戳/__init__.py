from nonebot import on_notice
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, PokeNotifyEvent, Message, MessageSegment


poke = on_notice()

@poke.handle()
async def _(bot: Bot, event: PokeNotifyEvent):
    if event.self_id == event.target_id:
        message = MessageSegment("poke", {"qq": str(event.user_id)})
        await poke.send(message=Message(message))
    await poke.finish()
