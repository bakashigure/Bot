import aiohttp
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message, MessageSegment
from nonebot import on_command
from . import qndxx_src
import threading
import asyncio
import yaml

yaml_file = './src/plugins/config/etc.yaml'

def read_config() -> dict:
    file = open(yaml_file, 'r', encoding='utf-8')
    raw_data = file.read()
    file.close()
    data = yaml.safe_load(raw_data)
    return data

cqndxx = ["催青年大学习", "cqndxx"]

this_plugin_name = "催青年大学习CQNDXX"
sx = on_command(
    "催青年大学习CQNDXX",
    aliases={*cqndxx},
    block=True
)

init = True

lock = False

@sx.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    global lock

    event_dict = event.dict()
    group_id = event_dict['group_id']
    raw_msg = event_dict['raw_message']
    
    data = read_config()
    data = data.get(group_id)
    if data == {}:
        await sx.finish()
        return

    # whether able to use now
    if lock == False:
        lock = True
        await sx.send("正在查询青年大学习，请等待2分钟哦")
    else:
        await sx.send("进程被占用了，请等待一会儿")
        await sx.finish()
        return

    username = data.get('qn_username', "")
    password = data.get('qn_password', "")
    student_list = data.get('qn_students', [])
    student_qq_dict = data.get('students_qq', {})

    async def q_func(bot, event):
        global lock, init
        try:
            q = qndxx_src.QNDXX(username, password, student_list, init)
            init = False
            q.login()
            q.goto_qndxx()
            q.search()
            res = q.get_absent()

            if q.error:
                lock = False
                await bot.send(
                    event=event,
                    message="查询失败！可能存在官网连接问题，如果多次失败请联系管理员排查问题。(error code: " + q.error_code + ")"
                )
                return

            res_list = [
                MessageSegment.text("还没有青年大学习的同学有：")
            ]

            if len(res) == 0:
                await bot.send(
                    event=event,
                    message="大家都参加了青年大学习啦！"
                )
            
            else:
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
                await bot.send(
                    event=event,
                    message=res_list[:-1]
                )
            
            if lock == True:
                lock = False
            
        except Exception as e:
            print(e)
            await bot.send(
                event=event,
                message="查询失败！如果多次失败请联系管理员排查问题。(Exception occurred)"
            )
            if lock == True:
                lock = False

    def for_async(bot, event):
        asyncio.run(q_func(bot, event))

    threading.Thread(target=for_async, args=(bot, event)).start()

    await sx.finish()
