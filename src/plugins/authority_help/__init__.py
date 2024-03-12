from nonebot import on_message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.rule import startswith
from nonebot.params import ShellCommandArgs
from nonebot.message import run_preprocessor
from nonebot.exception import IgnoredException
from nonebot.permission import SUPERUSER, SuperUser
from nonebot.plugin import on_shell_command, get_loaded_plugins
from nonebot.adapters.onebot.v11 import Bot, Event, MessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

from .util import parse
from ..config.plugin_config import (
    all_plugins_lists,
    normal_plugins,
    hidden_plugins,
)



# --- 1 ---

# this will run before every plugins, so you do not need to judge before every plugins

@run_preprocessor
async def _(matcher: Matcher, bot: Bot, event: Event):

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    # raw_msg = event_dict['raw_message']

    group_or_user_dict = { "group": group_id, "user": user_id }

    logger.debug(f"Checking authority for {matcher.plugin_name}")

    allow = False
    if matcher.plugin_name == "authority_help":
        allow = True
    else:
        for i_plugins in all_plugins_lists:
            if i_plugins.accessible(group_or_user_dict, matcher.plugin_name)[0]:
                allow = True
                break

    if allow:
        logger.debug(f"Authority admitted, {matcher.plugin_name} started")
        return
    else:
        logger.warning(f"Authority blocked, {matcher.plugin_name} cancelled")
        raise IgnoredException(f"Authority blocked, {matcher.plugin_name} cancelled")



# --- 2 ---

# 管理员更改 normal_plugins
# 1) 不含 hidden_plugins
# 2) 不含设置为 default（只有开和关）
# 3) 仅能设置群，不能设置私聊

authority_locker_order = ("开启", "打开", "启用", "关闭", "停用", "禁用")

authority_locker = on_message(
    rule=startswith(authority_locker_order),
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
)

@authority_locker.handle()
async def _(bot: Bot, event: MessageEvent):

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    raw_msg = event_dict["raw_message"]

    group_or_user_dict = { "group": group_id, "user": user_id }

    msg = parse(raw_msg, authority_locker_order)
    logger.debug(f"{msg}")

    order = msg[0]
    to_be_accessible = ("启" in order) or ("开" in order)

    plugin_list = msg[1:]

    if len(plugin_list) == 0:
        await authority_locker.finish()

    if (len(plugin_list) == 1) and plugin_list[0] in [
        "全部",
        "所有",
        "全部内容",
        "全部功能",
        "全部插件",
        "所有内容",
        "所有功能",
        "所有插件",
    ]:
        for name, _ in normal_plugins.plugin_name_dict.items():
            normal_plugins.change_access(group_or_user_dict, name, to_be_accessible)
        await authority_locker.send("注册的功能均已" + ("开启" if to_be_accessible else "关闭"))
        await authority_locker.finish()

    send_message = ""
    for single_plugin in plugin_list:
        plugin_name, plugin_id, exists = normal_plugins.parse(single_plugin)
        if plugin_id is None:
            send_message += "找不到名叫 [" + plugin_name + "] 的功能哦\n"
        elif plugin_name is None:
            send_message += "找不到代号为 [" + str(plugin_id) + "] 的功能哦\n"
        else:
            normal_plugins.change_access(group_or_user_dict, plugin_name, to_be_accessible)
            send_message += (
                "功能 ["
                + plugin_name
                + "] 已"
                + ("开启" if to_be_accessible else "关闭")
                + "\n"
            )

    await authority_locker.send(send_message.strip())
    await authority_locker.finish()



# --- 3 ---

# 开发者更改 normal_plugins, hidden_plugins
# 可设置为 default, open(true), close(false)
# 可在任何场合设置任意群和任意用户

config_modify_order = "config-modify"

config_modify_matcher = on_message(
    rule=startswith(config_modify_order), permission=SUPERUSER
)

@config_modify_matcher.handle()
async def _(bot: Bot, event: MessageEvent):
    if not SuperUser():
        await config_modify_matcher.finish()

    event_dict = event.dict()
    group_id = event_dict.get('group_id', None)
    user_id = event.get_user_id()
    raw_msg = event_dict["raw_message"]

    group_or_user = "user" if group_id is None else "group"
    group_or_user_id = user_id if group_id is None else group_id

    msg = parse(raw_msg, config_modify_order)
    args = msg[1:]

    logger.debug(f"{msg}")

    help_message = (
        "CONFIG-MODIFY MANUAL\n"
        "help\n"
        "\tconfig-modify [h(elp)]\n"
        "search\n"
        "\tconfig-modify s(earch)\n"
        "\tconfig-modify s(earch) a(ll)|u(ser)|g(roup)\n"
        "\tconfig-modify s(earch) u(ser)|g(roup) <id> [u(ser)|g(roup) <id> ...]\n"
        "update\n"
        "\tconfig-modify u(pdate) [u(ser)|g(roup) <id>] o(pen)|c(lose)|d(efault) a(ll) [h(idden)]\n"
        "\tconfig-modify u(pdate) [u(ser)|g(roup) <id>] o(pen)|c(lose)|d(efault) <plugin_name>|<plugin_id> [<plugin_name>|<plugin_id> ...]"
    )

    not_find_message = r"config-modify 中没有 {} 选项，请参见 `config-modify help`"
    wrong_message = r"config-modify 中 {} 的使用有误，请参见 `config-modify help`"


    def with_first_letter(*input: str):
        res = []
        for i in input:
            res.append(i)
            res.append(i[0])
        return res

    def get_global_name(var) -> str:
        name = [i for i, a in globals().items() if a == var][0]
        return name

    def ocd_to_tfd(ocd: str) -> str:
        if ocd == "o":
            return "t"
        elif ocd == "c":
            return "f"
        else:
            return "d"

    def tfd_to_output(tfd: str) -> str:
        if tfd == "t":
            return "开启"
        elif tfd == "f":
            return "关闭"
        else:
            return "设为默认"


    # config-modify [h(elp)]

    if len(args) == 0:
        await config_modify_matcher.send(help_message)
        await config_modify_matcher.finish()

    elif args[0] in with_first_letter("help"):
        await config_modify_matcher.send(help_message)
        await config_modify_matcher.finish()

    
    # config-modify s(earch)
    # config-modify s(earch) a(ll)|u(ser)|g(roup)
    # config-modify s(earch) u(ser)|g(roup) <id> [u(ser)|g(roup) <id> ...]

    elif args[0] in with_first_letter("search"):

        if len(args) == 1:
            send_message = ""
            for i_plugins in all_plugins_lists:
                send_message += "# " + get_global_name(i_plugins) + "\n"
                send_message += i_plugins.show(group_or_user, group_or_user_id)
            await config_modify_matcher.send(send_message.strip())
            await config_modify_matcher.finish()

        elif len(args) == 2 and args[1] in with_first_letter('all', 'user', 'group'):
            send_message = "<only show edited>\n"
            for i_plugins in all_plugins_lists:
                send_message += "# " + get_global_name(i_plugins) + "\n"
                send_message += i_plugins.show(args[1][0])
            await config_modify_matcher.send(send_message.strip())
            await config_modify_matcher.finish()

        else:
            ugid_pairs: list[tuple[str, str]] = list(zip(args[1::2], args[2::2]))
            send_message = ""

            for ug, id in ugid_pairs:

                if ug not in with_first_letter('user', 'group') or not id.isdigit():
                    await config_modify_matcher.send(wrong_message.format(args[0]))
                    await config_modify_matcher.finish()

                for i_plugins in all_plugins_lists:
                    send_message += "# " + get_global_name(i_plugins) + "\n"
                    send_message += i_plugins.show(ug[0], id)

            await config_modify_matcher.send(send_message.strip())
            await config_modify_matcher.finish()


    # config-modify u(pdate) [u(ser)|g(roup) <id>] o(pen)|c(lose)|d(efault) a(ll) [h(idden)]
    # config-modify u(pdate) [u(ser)|g(roup) <id>] o(pen)|c(lose)|d(efault) <plugin_name>|<plugin_id> [<plugin_name>|<plugin_id> ...]

    elif args[0] in with_first_letter("update"):

        if args[1] in with_first_letter("open", "close", "default"):
            here = True
            group_or_user_dict = { "group": group_id, "user": user_id }
            to_be_accessible = ocd_to_tfd(args[1][0])
            offset = 2

        elif args[1] in with_first_letter("user", "group") and args[2].isdigit():
            here = False
            group_or_user_dict = {
                "group": args[2] if args[1] in with_first_letter("group") else None,
                "user": args[2] if args[1] in with_first_letter("user") else None,
            }
            to_be_accessible = ocd_to_tfd(args[3][0])
            offset = 4

        else:
            await config_modify_matcher.send(wrong_message.format(args[0]))
            await config_modify_matcher.finish()

        if args[offset + 0] in with_first_letter('all'):
            send_message = ""
            if not here:
                send_message = ("群 " if args[1] in with_first_letter('group') else "用户 ") + args[2]
            if len(args) == offset + 2 and args[offset + 1] in with_first_letter('hidden'):
                for name, _ in hidden_plugins.plugin_name_dict.items():
                    hidden_plugins.change_access(group_or_user_dict, name, to_be_accessible)
                await config_modify_matcher.send(
                    send_message + f" 所有隐藏功能均已{tfd_to_output(to_be_accessible)}"
                )
                await config_modify_matcher.finish()
            elif len(args) == offset + 1:
                for name, _ in normal_plugins.plugin_name_dict.items():
                    normal_plugins.change_access(group_or_user_dict, name, to_be_accessible)
                await config_modify_matcher.send(
                    send_message + f" 所有功能均已{tfd_to_output(to_be_accessible)}"
                )
                await config_modify_matcher.finish()
            else:
                await config_modify_matcher.send(wrong_message.format(args[0]))
                await config_modify_matcher.finish()

        else:
            plugin_list = args[offset:]
            send_message = ""
            if not here:
                send_message = ("群 " if args[1] in with_first_letter('group') else "用户 ") + args[2] + '\n'
            for single_plugin in plugin_list:
                hidden_prefix = ""
                plugin_name, plugin_id, exists = normal_plugins.parse(single_plugin)
                if not exists:
                    plugin_name, plugin_id, exists = hidden_plugins.parse(single_plugin)
                    hidden_prefix = "隐藏"
                if plugin_id is None:
                    send_message += f"找不到名叫 [{plugin_name}] 的功能哦\n"
                elif plugin_name is None:
                    send_message += f"找不到代号为 [{plugin_id}] 的功能哦\n"
                else:
                    normal_plugins.change_access(
                        group_or_user_dict, plugin_name, to_be_accessible
                    )
                    hidden_plugins.change_access(
                        group_or_user_dict, plugin_name, to_be_accessible
                    )
                    send_message += f"{hidden_prefix}功能 [{plugin_name}] 已{tfd_to_output(to_be_accessible)}\n"
            await config_modify_matcher.send(send_message.strip())
            await config_modify_matcher.finish()


    # not find

    else:
        await config_modify_matcher.send(not_find_message.format(args[0]))
        await config_modify_matcher.finish()
