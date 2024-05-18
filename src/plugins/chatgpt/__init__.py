import re
import yaml
import httpx
import traceback
from openai import AsyncOpenAI
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_hammer_core.util.message_factory import reply_text

from .gptlogger import gptlogger

gpt_catcher = on_regex(r"^gpt(s|c|h)?[ \t]*(?:\r?\n((?:.|\s)*?))?$")

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

    name_prefix = ("(message from qq=" + user_id + "): ") if group_id is not None else ""
    history_prefix = ""
    history_used = False

    history.setdefault(guid, '')

    content_list = re.findall(r"^gpt(s|c|h)?[ \t]*(?:\r?\n((?:.|\s)*?))?$", raw_msg)[0]
    content = content_list[1].strip()

    gptlogger.info("get message\n" + event.get_log_string() + "\nmethod (s|c|h|nothing): " + content_list[0])

    if content_list[0] == "h":
        await gpt_catcher.send("gpth: 显示帮助\ngpt<换行>内容: 不使用历史记录\ngpts<换行>内容: 使用历史记录\ngptc<换行>内容: 清空历史且不使用历史记录\n")


    if content == "":

        if content_list[0] == "c":
            history[guid] = ''
            await gpt_catcher.send("历史记录已清除")

        else:
            pass

        await gpt_catcher.finish()

    else:

        if content_list[0] == "c":
            history_used = False
            history[guid] = ''
            history_prefix = "(历史记录已清除)\n"

        elif content_list[0] == "s":
            history_used = True

        elif content_list[0] == "":
            history_used = False
            history_prefix = "(本次无历史)\n"

        else:
            await gpt_catcher.finish()


    client = AsyncOpenAI(
        api_key=yaml_read['api_key'],
        base_url=yaml_read['base_url'],
        timeout=httpx.Timeout(120.0)
    )

    model_name = "gpt-4o"
    
    try:
        if history_used:

            completion = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "" + ("You are now talking with many people." if group_id is not None else "")},
                    {"role": "user", "content": "history message (may be cut):\n\n" + history[guid] + "\n\ncurrent message:\n\n" + name_prefix + content}
                ],
            )

        else:

            completion = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": content}
                ],
            )

    except Exception as e:
        gptlogger.error("send message to\n" + event.get_log_string() + "\n" + str(e) + "\n" + traceback.format_exc())
        await gpt_catcher.send(reply_text(f"网络不畅，请稍后重试。\n错误内容: {e}", event))
        await gpt_catcher.finish()

    result = completion.choices[0].message.content
    history[guid] += name_prefix + content + "\n\n\n" + result + "\n\n\n"
    history[guid] = history[guid][-2000:]

    gptlogger.info("send message to\n" + event.get_log_string() + "\n" + history_prefix + result)
    await gpt_catcher.send(reply_text(history_prefix + result, event))
    await gpt_catcher.finish()
