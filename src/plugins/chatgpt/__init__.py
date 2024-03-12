import re
import yaml
from openai import AsyncOpenAI
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_hammer_core.util.message_factory import reply_text

gpt_catcher = on_regex(r"^gpt\r?\n((?:.|\s)*?)$")

with open("./src/plugins/chatgpt/gpt.yaml", 'r', encoding='utf-8') as file:
    yaml_read = yaml.safe_load(file.read())

history = dict()

@gpt_catcher.handle()
async def _(bot: Bot, event: Event):

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    raw_msg = event_dict['raw_message']
    guid = ("g" + str(group_id)) if group_id is not None else ("u" + user_id)

    history.setdefault(guid, '')

    content = re.findall(r"^gpt\r?\n((?:.|\s)*?)$", raw_msg)[0]

    client = AsyncOpenAI(
        api_key=yaml_read['api_key'],
        base_url=yaml_read['base_url']
    )

    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "history message (may be cut): " + history[guid] + "\n\n\n\n current message: " + content}
        ]
    )

    result = completion.choices[0].message.content
    history[guid] += content + "\n\n" + result
    history[guid] = history[guid][-2000:]

    await gpt_catcher.send(reply_text(result, event))
    await gpt_catcher.finish()
