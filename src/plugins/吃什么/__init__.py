import re
import os
import json
import random
from pathlib import Path
from nonebot.log import logger
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

your_plugin_catcher = on_regex("^今天吃什么(?:|\.|。|！|!|？|\?)*$")


@your_plugin_catcher.handle()
async def _(bot: Bot, event: Event):
    recipe_dir = Path('./src/plugins/dataset/recipe')
    s = next(os.walk(recipe_dir))
    # s: [name, [dirs], [files]]
    recipe_filename = random.choice(s[2])
    with open(recipe_dir / recipe_filename, 'r') as recipe_file:
        recipe_json = json.load(recipe_file)
        # recipe_json.sort(key=lambda x: len(x.get('title', '')))
        # recipe_json.reverse()
        k = random.choice(recipe_json)
        name: str = k.get('title', '白饭')
        logger.debug(name)
        name = name.split("，")[0]
        name = name.split(",")[0]
        print(name)

    reply = f'今天吃{name}'
    await your_plugin_catcher.send(reply)
    await your_plugin_catcher.finish()
