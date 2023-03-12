import aiohttp
import nonebot
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message, MessageSegment
from nonebot import on_command
from nonebot import require
from . import yqtb_src
import threading
import asyncio
import yaml

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

yaml_file = './src/plugins/config/etc.yaml'

def read_config() -> dict:
    file = open(yaml_file, 'r', encoding='utf-8')
    raw_data = file.read()
    file.close()
    data = yaml.safe_load(raw_data)
    return data

cyqtb = ["催疫情填报", "cyqtb"]

this_plugin_name = "催疫情填报CYQTB"
sx = on_command(
    "催疫情填报CYQTB",
    aliases={*cyqtb},
    block=True
)

init = True


# 主函数，主线程与自动化均会使用
async def normal_handle(bot, *, automatic, event = None, group_id = None):

    # group_id is different in auto or mannual
    if not automatic:
        event_dict = event.dict()
        group_id = event_dict['group_id']
        # raw_msg = event_dict['raw_message']
    
    # identify group permission
    data = read_config()
    data = data.get(group_id, {})
    if data == {}:
        if not automatic: await sx.finish()
        return

    # 手动查询时提供反馈
    if not automatic:
        await bot.send(
            message="正在查询疫情填报，请等待数秒钟",
            event=event
        )

    # 载入数据
    username = data.get('yq_username', "")
    password = data.get('yq_password', "")
    student_list = data.get('yq_students', [])
    student_qq_dict = data.get('students_qq', {})

    # 查询函数（由于比较慢，采用独立线程回调而非占用 bot 的主线程）
    async def q_func(bot, event, group_id):

        try:
            global init
            # 调用自己的疫情填报库
            q = yqtb_src.YQTB(username, password, student_list, init)
            init = False
            res = q.run().get_absent()

            # 输出
            if len(res) == 0:
                if not automatic:
                    await bot.send(
                        message="大家都进行疫情填报了！",
                        event=event
                    )
                else:
                    await bot.send_group_msg(
                        message="大家都进行疫情填报了！",
                        group_id=group_id
                    )
            else:
                res_list = [
                    MessageSegment.text("还没有疫情填报的同学有：")
                ]
                for mem in res:
                    qq = student_qq_dict.get(mem, "")
                    if qq == "":
                        res_list.append(
                            MessageSegment.text(mem)
                        )
                        res_list.append(
                            MessageSegment.text("，")
                        )
                    else:
                        res_list.append(
                            MessageSegment.at(qq)
                        )
                        res_list.append(
                            MessageSegment.text("，")
                        )
                if not automatic:
                    await bot.send(
                        message=res_list[:-1],
                        event=event
                    )
                else:
                    await bot.send_group_msg(
                        message=res_list[:-1],
                        group_id=group_id
                    )
        
        except Exception as e:
            print(e)
            if not automatic:
                await bot.send(
                    message="查询填报失败，请手动尝试或请联系管理员处理。",
                    event=event
                )
            else:
                await bot.send_group_id(
                    message="自动查询填报失败，请手动尝试或请联系管理员处理。",
                    group_id=group_id
                )

    # 独立线程打包（异步函数内，开一个 thread 需要这样用）
    def for_async(bot, event, group_id):
        asyncio.run(q_func(bot, event, group_id))

    # 独立线程
    threading.Thread(target=for_async, args=(bot, event, group_id)).start()

    # 主线程结束
    if not automatic:
        await sx.finish()


# 以下是 schedule 内容

# 班级群中午提醒
# @scheduler.scheduled_job(trigger='cron', hour='12', minute='20', second='00')
# async def _():
#     await normal_handle(list(nonebot.get_bots().values())[0], automatic=True, group_id=593456235)

# 班级群下午提醒
# @scheduler.scheduled_job(trigger='cron', hour='18', minute='50', second='00')
# async def _():
#     await normal_handle(list(nonebot.get_bots().values())[0], automatic=True, group_id=593456235)

# 大群下午提醒
# @scheduler.scheduled_job(trigger='cron', hour='17', minute='40', second='00')
# async def _():
#     await normal_handle(list(nonebot.get_bots().values())[0], automatic=True, group_id=881054187)

# 大群晚间提醒
# @scheduler.scheduled_job(trigger='cron', hour='21', minute='30', second='00')
# async def _():
#     await normal_handle(list(nonebot.get_bots().values())[0], automatic=True, group_id=881054187)


# 主线程，由于会自动化，所以采用一个单独的函数
@sx.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await normal_handle(bot, automatic=False, event=event)
