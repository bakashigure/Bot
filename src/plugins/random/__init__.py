import re
import random
from nonebot import on_message
from nonebot.rule import startswith
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot_plugin_hammer_core.util.message_factory import reply_text

random_matcher = on_message(rule=startswith(("random", "随机数", "随机")))

@random_matcher.handle()
async def _(bot: Bot, event: MessageEvent):

    raw_msg = event.dict()['raw_message']
    content = list(re.findall('^(?:random|随机数|随机)[:：，,\s]*(-?[\d]*)[:：，,\s]*(-?[\d]*)', raw_msg)[0])

    if not content[0]:
        a, b = random.random() * 10, random.random() * 10
        if a != 0 and b != 0:
            await random_matcher.send(reply_text(
                '{}{:.2f} {} {:.2f}i'.format(
                    "" if (random.randint(0, 1) == 0) else "- ", a,
                    "+" if (random.randint(0, 1) == 0) else "-", b
                ), event
            ))
        elif a == 0 and b != 0:
            await random_matcher.send(reply_text(
                '{}{:.2f}i'.format(
                    "" if (random.randint(0, 1) == 0) else "- ", b
                ), event
            ))
        elif a != 0 and b == 0:
            await random_matcher.send(reply_text(
                '{}{:.2f}'.format(
                    "" if (random.randint(0, 1) == 0) else "- ", a,
                ), event
            ))
        else:
            await random_matcher.send(reply_text("0"), event)
    
    else:
        a = int(content[0])
        if not content[1]:
            if a >= 1:
                b = 1
            else:
                b = 0
        else:
            b = int(content[1])
        if a > b:
            a, b = b, a
        await random_matcher.send(reply_text(
            f"{random.randint(a, b)}", event
        ))
    
    await random_matcher.finish()
