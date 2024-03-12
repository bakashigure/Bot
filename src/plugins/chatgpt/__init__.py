import re
import yaml
from openai import OpenAI
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

gpt_catcher = on_regex(r"^gpt\r?\n((?:.|\s)*?)$")

with open("./src/plugins/chatgpt/gpt.yaml", 'r', encoding='utf-8') as file:
    yaml_read = yaml.safe_load(file.read())

@gpt_catcher.handle()
async def _(bot: Bot, event: Event):

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    raw_msg = event_dict['raw_message']

    content = re.findall(r"^gpt\r?\n((?:.|\s)*?)$", raw_msg)[0]

    client = OpenAI(
        api_key=yaml_read['api_key'],
        base_url=yaml_read['base_url']
    )

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": content}
        ]
    )

    await gpt_catcher.send(completion.choices[0].message)
    await gpt_catcher.finish()
