from nonebot import on_message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.rule import startswith
from nonebot.permission import SUPERUSER, SuperUser
from nonebot.params import ShellCommandArgs
from nonebot.message import run_preprocessor
from nonebot.exception import IgnoredException
from nonebot.plugin import on_shell_command, get_loaded_plugins

from nonebot.adapters.onebot.v11 import Bot, Event, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

from .util import parse
from ..config.plugin_config import plugin_config, hidden_plugin_config, all_plugin_config_list


# this will run before every plugins, so you do not need to judge before every plugins
@run_preprocessor
async def _(matcher: Matcher, bot: Bot, event: Event):

    group_or_user_id = {
        "user": event.user_id if hasattr(event, "user_id") else None,
        "group": event.group_id if hasattr(event, "group_id") else None,
    }

    logger.debug(f"Checking authority for {matcher.plugin_name}")

    allow = False
    if matcher.plugin_name == "authority_help":
        allow = True
    else:
        for i_plugin_config in all_plugin_config_list:
            if i_plugin_config.accessible(group_or_user_id, matcher.plugin_name)[0]:
                allow = True
                break

    if allow:
        logger.debug(f"Authority admitted, {matcher.plugin_name} started")
        return
    else:
        logger.warning(f"Authority blocked, {matcher.plugin_name} cancelled")
        raise IgnoredException(f"Authority blocked, {matcher.plugin_name} cancelled")


authority_locker_order = ("开启", "打开", "启用", "关闭", "停用", "禁用")

# 用以修改 plugin_config (PluginConfig 的一个实例，不包含 hidden_plugin_config)
authority_locker = on_message(
    rule=startswith(authority_locker_order),
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER
)

all_authority_locker_order = "config-modify"

# 用以修改 all_plugin_config_list 中包含的所有文件
all_authority_locker = on_message(
    rule=startswith(all_authority_locker_order),
    permission=SUPERUSER
)


@authority_locker.handle()
async def _(bot: Bot, event: MessageEvent):

    group_or_user_id = {
        "user": event.user_id if hasattr(event, "user_id") else None,
        "group": event.group_id if hasattr(event, "group_id") else None,
    }

    raw_msg = event.dict()['raw_message']
    msg = parse(raw_msg, authority_locker_order)
    logger.debug(f"{msg}")

    order = msg[0]
    to_be_accessible = ('启' in order) or ('开' in order)

    plugin_list = msg[1:]

    if len(plugin_list) == 0:
        await authority_locker.finish()
        return

    if (len(plugin_list) == 1) and plugin_list[0] in ["全部", "所有", "全部内容", "全部功能", "全部插件", "所有内容", "所有功能", "所有插件"]:
        for (name, tup) in plugin_config.plugin_name_dict.items():
            plugin_config.change_access(group_or_user_id, name, to_be_accessible)
        await authority_locker.send("注册的功能均已" + ("开启" if to_be_accessible else "关闭"))
        await authority_locker.finish()
        return

    send_message = ""
    for single_plugin in plugin_list:
        plugin_name, plugin_id, exists = plugin_config.parse(single_plugin)
        if plugin_id is None:
            send_message += "找不到名叫 [" + plugin_name + "] 的功能哦\n"
        elif plugin_name is None:
            send_message += "找不到代号为 [" + str(plugin_id) + "] 的功能哦\n"
        else:
            plugin_config.change_access(group_or_user_id, plugin_name, to_be_accessible)
            send_message += "功能 [" + plugin_name + "] 已" + ("开启" if to_be_accessible else "关闭") + "\n"
    
    await authority_locker.send(send_message.strip())
    await authority_locker.finish()



@all_authority_locker.handle()
async def _(bot: Bot, event: MessageEvent):

    if not SuperUser():
        await all_authority_locker.finish()
        return
    
    raw_msg = event.dict()['raw_message']
    msg = parse(raw_msg, all_authority_locker_order)
    logger.debug(f"{msg}")

    arguments = msg[1:]

    help_message = "CONFIG-MODIFY MANUAL\n" \
        "(1) config-modify help\n" \
        "(2) config-modify search [u(ser)|g(roup)|a(ll) [<qq_id>]] \n" \
        "(3) config-modify update u(ser)|g(roup) <qq_id> oa|ca|da [hidden]\n" \
        "(4) config-modify update u(ser)|g(roup) <qq_id> open|close|default <plugin_name>|<plugin_id> [<plugin_name>|<plugin_id> ...]"
    
    not_find_message = r"config-modify 中没有 {} 选项，请参见 'config-modify help'"
    wrong_message = r"config-modify 中 {} 的使用有误，请参见 'config-modify help'"

    def get_global_name(var) -> str:
        name = [ i for i, a in globals().items() if a == var][0]
        return name

    if len(arguments) == 0:
        await all_authority_locker.send(help_message)
        await all_authority_locker.finish()
        return

    elif arguments[0] == "help":
        await all_authority_locker.send(help_message)
        await all_authority_locker.finish()
        return

    elif arguments[0] == "search":
        if len(arguments) == 1 or ( \
            (len(arguments) == 2 or (len(arguments) == 3 and arguments[2].isdigit())) and \
            arguments[1] in ['u', 'user', 'g', 'group', 'a', 'all'] \
        ):
            send_message = ""
            for i_plugin_config in all_plugin_config_list:
                send_message += "\n# " + get_global_name(i_plugin_config) + "\n"
                send_message += i_plugin_config.show(
                    'a' if len(arguments) == 1 else arguments[1],
                    None if len(arguments) != 3 else int(arguments[2])
                )
            await all_authority_locker.send(send_message.strip())
            await all_authority_locker.finish()
            return
        # wrong
        else:
            await all_authority_locker.send(wrong_message.format(arguments[0]))
            await all_authority_locker.finish()
            return

    elif arguments[0] == "update":
        if len(arguments) >= 4 and \
            arguments[1] in ['u', 'user', 'g', 'group'] and \
            arguments[2].isdigit() and \
            ((arguments[3] in ['open', 'close', 'default'] and len(arguments) > 4) or \
            (arguments[3] in ['oa', 'ca', 'da'] and (len(arguments) == 4 or (len(arguments) == 5 and arguments[4] == "hidden")))):
            group_or_user_id = {
                "group": int(arguments[2]) if arguments[1] in ['g', 'group'] else None,
                "user": int(arguments[2]) if arguments[1] in ['u', 'user'] else None
            }
            def ocd_to_tfd(ocd: str) -> str:
                if ocd == "o": return 't'
                elif ocd == "c": return 'f'
                else: return 'd'
            def tfd_to_output(tfd: str) -> str:
                if tfd == "t": return '开启'
                elif tfd == "f": return '关闭'
                else: return '设为默认'
            to_be_accessible = ocd_to_tfd(arguments[3][0])
            if arguments[3] in ['oa', 'ca', 'da'] and len(arguments) == 4 or (len(arguments) == 5 and arguments[4] == "hidden"):
                if len(arguments) == 4:
                    for (name, tup) in plugin_config.plugin_name_dict.items():
                        plugin_config.change_access(group_or_user_id, name, to_be_accessible)
                    await all_authority_locker.send(
                        ("群" if arguments[1] in ['g', 'group'] else "用户") +
                        f" {int(arguments[2])} 所有功能均已" +
                        tfd_to_output(to_be_accessible)
                    )
                    await all_authority_locker.finish()
                else:
                    for (name, tup) in hidden_plugin_config.plugin_name_dict.items():
                        hidden_plugin_config.change_access(group_or_user_id, name, to_be_accessible)
                    await all_authority_locker.send(
                        ("群" if arguments[1] in ['g', 'group'] else "用户") +
                        f" {int(arguments[2])} 所有隐藏功能均已" +
                        tfd_to_output(to_be_accessible)
                    )
                    await all_authority_locker.finish()
            else:
                plugin_list = arguments[4:]
                send_message = ("群" if arguments[1] in ['g', 'group'] else "用户") + f" {int(arguments[2])}\n"
                for single_plugin in plugin_list:
                    hidden_prefix = ""
                    plugin_name, plugin_id, exists = plugin_config.parse(single_plugin)
                    if not exists:
                        plugin_name, plugin_id, exists = hidden_plugin_config.parse(single_plugin)
                        hidden_prefix = "隐藏"
                    if plugin_id is None:
                        send_message += "找不到名叫 [" + plugin_name + "] 的功能哦\n"
                    elif plugin_name is None:
                        send_message += "找不到代号为 [" + str(plugin_id) + "] 的功能哦\n"
                    else:
                        plugin_config.change_access(group_or_user_id, plugin_name, to_be_accessible)
                        hidden_plugin_config.change_access(group_or_user_id, plugin_name, to_be_accessible)
                        send_message += hidden_prefix + "功能 [" + plugin_name + "] 已" + tfd_to_output(to_be_accessible) + "\n"
                await all_authority_locker.send(send_message.strip())
                await all_authority_locker.finish()
        # wrong
        else:
            await all_authority_locker.send(wrong_message.format(arguments[0]))
            await all_authority_locker.finish()
            return
    
    # not find
    else:
        await all_authority_locker.send(not_find_message.format(arguments[0]))
        await all_authority_locker.finish()
        return
