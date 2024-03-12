import re
from nonebot import on_message
from nonebot.rule import startswith
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from ..config.plugin_config import normal_plugins

help_matcher = on_message(rule=startswith(('help', 'Help', '帮助', 'man', 'Man')))

'''
help 只会处理 normal_plugins 中注册的插件
'''

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def show_readme(plugin_name: str) -> str:
    readme_file_path = './src/plugins/' + plugin_name + '/readme.md'
    readme_file = open(readme_file_path, "r+")
    readme = readme_file.read()
    content = re.findall('\*可显示部分开始\*\n\n([\s\S]*?)\n\n\*可显示部分中止\*', readme)
    if content:
        readme = content[0].replace('> ', '').replace('#### ', '')
    else:
        readme = "暂无可显示的介绍"
    return readme


@help_matcher.handle()
async def _(bot: Bot, event: MessageEvent):

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    raw_msg = event_dict['raw_message']

    group_or_user_dict = { "group": group_id, "user": user_id }

    content = re.findall('^(?:[hH]elp|帮助|man)[:：，,\s]*([\S]*)', raw_msg)[0]

    if not content:
        # 单独使用 man 是不行的
        if 'man' in raw_msg:
            await help_matcher.finish()
            return
        msg = '可用的命令有\n\n'
        for plugin_id, plugin_name in normal_plugins.items():
            msg += '(' + str(plugin_id) + ")\t" + plugin_name + "\t" \
                + ("已开启" if normal_plugins.accessible(group_or_user_dict, plugin_name)[0] else "已关闭") + "\n"
        msg += '\n使用 `man [名称]` 获取各个命令的详细帮助'
        msg += '\n作者可使用 `config-modify` 直接控制开关'
        await help_matcher.send(msg)

    elif is_number(content):
        name = normal_plugins.get_name(int(float(content)))
        if name != None:
            await help_matcher.send(show_readme(name))
        else:
            await help_matcher.send("未找到" + content + "号命令")

    else:
        pid = normal_plugins.get_id(content)
        if pid != None:
            await help_matcher.send(show_readme(content))
        else:
            await help_matcher.send("未找到与" + content + "相关的命令")

    await help_matcher.finish()
