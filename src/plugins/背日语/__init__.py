import re
import json
import time
import random
import timeit
import asyncio
import threading

from pathlib import Path
from collections import defaultdict

from nonebot import on_command, on_message
from nonebot.rule import Rule
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot_plugin_hammer_core.util.message_factory import reply_text


data_root = "./src/plugins/dataset/nihongo"
file_list = ["n1", "n2", "n3", "n5n4"]


word_list = defaultdict(list)  # []
word = defaultdict(dict)  # {}
is_testing_hyou = defaultdict(bool)  # False
now_index = defaultdict(int)  # 0
start = defaultdict(int)  # 0
lock = defaultdict(int)  # 0


async def is_valid(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    global is_testing_hyou, now_index, word, start, word_list
    group_id = event.dict().get("group_id", 0)
    return not is_testing_hyou[group_id]


async def is_ans(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    global is_testing_hyou, now_index, word, start, word_list
    group_id = event.dict().get("group_id", 0)
    return is_testing_hyou[group_id]


this_plugin_name = "背日语"
Nihongo_catcher = on_command("背日语", rule=Rule(is_valid))


class TimerAns:
    def __init__(self, bot, event, group_id):
        self.event = event
        self.bot = bot
        self.group_id = group_id
        self.begin_tick = timeit.default_timer()
        self.used0 = False
        self.used1 = False
        self.used2 = False
        self.used3 = False
        self.timeout = False
        self.next_end = False
        self.end = False

    async def loop(self):
        global is_testing_hyou, now_index, word, start, word_list
        while True:
            global Nihongo_catcher
            tick = timeit.default_timer() - self.begin_tick
            if self.end:
                self.end = self.next_end
                self.next_end = False
                break
            elif tick >= 10 and not self.used0:
                self.used0 = True
                await self.bot.send(
                    event=self.event,
                    message="10s提示：词性为"
                    + re.findall(
                        re.compile(r"(【.*?】)"), word[self.group_id].get("res")
                    )[0],
                )
            elif tick >= 30 and not self.used1:
                self.used1 = True
                await self.bot.send(
                    event=self.event,
                    message="30s提示：长度为"
                    + str(
                        len(
                            word[self.group_id]
                            .get("name")
                            .replace("～", "")
                            .split("/")[0]
                        )
                    ),
                )
            elif tick >= 50 and not self.used2:
                self.used2 = True
                await self.bot.send(
                    event=self.event,
                    message="50s提示：开头为【"
                    + word[self.group_id].get("name").replace("～", "").split("/")[0][0]
                    + "】",
                )
            elif tick >= 60 and not self.used3:
                self.used3 = True
                await self.bot.send(
                    event=self.event,
                    message="已超时，答题退出\n" + "正确答案为\n"
                    "【"
                    + str(now_index[self.group_id])
                    + "】"
                    + word[self.group_id].get("name")
                    + word[self.group_id].get("res"),
                )
                self.timeout = True
                is_testing_hyou[self.group_id] = False
                break

    def for_async(self):
        asyncio.run(self.loop())
        # r = asyncio.new_event_loop()
        # asyncio.set_event_loop(r)
        # r.run_until_complete(self.loop())
        # r.close()

    def begin_loop(self):
        threading.Thread(target=self.for_async, args=(), daemon=True).start()

    async def show_question(self):
        global is_testing_hyou, now_index, word, start, word_list
        now_index[self.group_id] += 1
        start[self.group_id] = timeit.default_timer()
        num = random.randint(0, len(word_list[self.group_id]) - 1)
        word[self.group_id] = word_list[self.group_id][num]

        kanares = list(re.findall("^（(.*?)）", word[self.group_id]["res"]))
        if len(kanares) != 0:
            kanares = kanares[0]
        if len(kanares) == 0 or kanares == "":
            kanares = None

        word[self.group_id]["kanares"] = kanares

        print(word)

        await self.bot.send(
            event=self.event,
            message="【"
            + str(now_index[self.group_id])
            + "】"
            + word[self.group_id].get("desc"),
        )

    def reset_loop(self):
        self.begin_tick = timeit.default_timer()
        self.used0 = False
        self.used1 = False
        self.used2 = False
        self.used3 = False
        self.next_end = False

    def stop_loop(self):
        self.end = True


TA = defaultdict(TimerAns)  # 0


@Nihongo_catcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    global is_testing_hyou, now_index, word, start, word_list
    group_id = event.dict().get("group_id", 0)
    event_dict = event.dict()
    user_id = event.get_user_id()
    is_testing_hyou[group_id] = False
    await Nihongo_catcher.send(
        reply_text("请选择题库：\n1, N1\n2, N2\n3, N3\n4, N4N5", event)
    )


@Nihongo_catcher.got("选库")
async def get_setu(bot: Bot, event: GroupMessageEvent, state: T_State):
    global is_testing_hyou, now_index, word, start, word_list
    group_id = event.dict().get("group_id", 0)
    event_dict = event.dict()
    id = int(event_dict["raw_message"].strip())
    if 1 <= id <= 4:
        get(id - 1, group_id)
        is_testing_hyou[group_id] = True
        this_group_id = event_dict.get("group_id", 0)
        now_index[group_id] = 0
        await Nihongo_catcher.send(
            reply_text("共" + str(len(word_list[group_id])) + "个词汇，即将随机出题", event)
        )

        # word_catcher
        TA[group_id] = TimerAns(bot, event, group_id)
        await TA[group_id].show_question()
        TA[group_id].begin_loop()
        # word_catcher

        await Nihongo_catcher.finish()

    else:
        is_testing_hyou[group_id] = False
        Nihongo_catcher.send(reply_text("题库范围错误", event))
        await Nihongo_catcher.finish()


def get(choice: int, group_id: int) -> None:
    global is_testing_hyou, now_index, word, start, word_list
    word_list[group_id].clear()
    path_file = Path(data_root) / file_list[choice]
    # print(path_file)
    if not path_file.exists():
        return
    gen = [i for i in path_file.iterdir()]
    for json_file in gen:
        if json_file.suffix != ".json":
            continue
        # print(json_file.suffix, json_file)
        with open(json_file, mode="r", encoding="utf-8") as f:
            data_dict = json.load(f)
            res = data_dict["data"]
            for i in res:
                word_list[group_id].append(
                    {
                        "name": i["wordName"],
                        "desc": i["correctDesc"],
                        "res": i["wordDesc"],
                    }
                )


ans_catcher = on_message(rule=Rule(is_ans), priority=1)


@ans_catcher.handle()
async def ans_handle(bot: Bot, event: GroupMessageEvent, state: T_State):
    global is_testing_hyou, now_index, word, start, word_list
    group_id = event.dict().get("group_id", 0)

    if lock[group_id] or TA[group_id].timeout:
        await ans_catcher.finish()
        return

    elif (
        event.dict()["raw_message"].strip()
        in word[group_id]["name"].replace("～", "").split("/")
        or event.dict()["raw_message"].strip() == word[group_id]["kanares"]
    ):
        lock[group_id] = True
        await ans_catcher.send(
            reply_text(
                f"答对了！\n【{now_index[group_id]}】{word[group_id]['name']}{word[group_id]['res']}",
                event,
            )
        )

        # word_catcher
        TA[group_id].stop_loop()
        TA[group_id].reset_loop()
        await TA[group_id].show_question()
        TA[group_id].begin_loop()
        # word_catcher

    elif event.dict()["raw_message"].strip() in [
        "知らない",
        "しらない",
        "分からない",
        "わからない",
        "不会",
        "不知道",
    ]:
        lock[group_id] = True
        await ans_catcher.send(
            reply_text(
                f"公布答案\n【{now_index[group_id]}】{word[group_id]['name']}{word[group_id]['res']}\n要认真记住哦",
                event,
            )
        )

        # word_catcher
        TA[group_id].stop_loop()
        TA[group_id].reset_loop()
        await TA[group_id].show_question()
        TA[group_id].begin_loop()
        # word_catcher

    elif event.dict()["raw_message"].strip() in ["不背了", "停止背诵"]:
        lock[group_id] = True
        await ans_catcher.send("欢迎下次使用哦")
        TA[group_id].stop_loop()
        is_testing_hyou[group_id] = False

    lock[group_id] = False
    await ans_catcher.finish()
