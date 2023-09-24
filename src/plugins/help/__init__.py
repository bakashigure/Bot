import re
from nonebot import on_message
from nonebot.rule import startswith
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from ..config.plugin_config import plugin_config

help_matcher = on_message(rule=startswith(('help', 'Help', '帮助', 'man', 'Man')))

'''
help 只会处理 plugin_config 中注册的插件
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

    group_or_user_id = {
        "user": event.user_id if hasattr(event, "user_id") else None,
        "group": event.group_id if hasattr(event, "group_id") else None,
    }

    raw_msg = event.dict()['raw_message']
    content = re.findall('^(?:[hH]elp|帮助|man)[:：，,\s]*([\S]*)', raw_msg)[0]

    if not content:
        # 单独使用 man 是不行的
        if 'man' in raw_msg:
            await help_matcher.finish()
            return
        msg = '可用的命令有\n\n'
        for plugin_id, plugin_name in plugin_config.items():
            msg += '(' + str(plugin_id) + ")\t" + plugin_name + "\t" \
                + ("已开启" if plugin_config.accessible(group_or_user_id, plugin_name)[0] else "已关闭") + "\n"
        msg += '\n使用 `man [名称]` 获取各个命令的详细帮助'
        msg += '\n管理者可使用 `config-modify` 直接控制开关'
        await help_matcher.send(msg)
    
    elif is_number(content):
        name = plugin_config.get_name(int(float(content)))
        if name != None:
            await help_matcher.send(show_readme(name))
        else:
            await help_matcher.send("未找到" + content + "号命令")
    
    else:
        pid = plugin_config.get_id(content)
        if pid != None:
            await help_matcher.send(show_readme(content))
        else:
            await help_matcher.send("未找到与" + content + "相关的命令")

    await help_matcher.finish()
