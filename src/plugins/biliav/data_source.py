import httpx
import json
import re
import nonebot
from nonebot.adapters.onebot.v11 import MessageSegment

url: str = 'https://api.bilibili.com/x/web-interface/view'

global_config = nonebot.get_driver().config
config = global_config.dict()
b_comments = config.get('b_comments', False)
# b_b23tv = config.get('b_b23tv', True)

if type(b_comments) != bool and b_comments == "True":
    b_comments = True
else:
    b_comments = False

# if type(b_b23tv) != bool and b_b23tv == "False":
#     b_b23tv = False
# else:
#     b_b23tv = True

# import math


async def b23tv2bv(b23tv: str) -> str:
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = await client.get('https://' + b23tv, headers=headers)
    return re.findall("[Bb][Vv]1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2}", str(r.next_request.url))[0]

"""
async def bv2av(Bv: str) -> int:
    # 1.去除Bv号前的"Bv"字符
    BvNo1: str = Bv[2:]
    keys: dict[str:str] = {
        '1': '13', '2': '12', '3': '46', '4': '31', '5': '43', '6': '18', '7': '40', '8': '28', '9': '5',
        'A': '54', 'B': '20', 'C': '15', 'D': '8', 'E': '39', 'F': '57', 'G': '45', 'H': '36', 'J': '38', 'K': '51',
        'L': '42', 'M': '49', 'N': '52', 'P': '53', 'Q': '7', 'R': '4', 'S': '9', 'T': '50', 'U': '10', 'V': '44',
        'W': '34', 'X': '6', 'Y': '25', 'Z': '1',
        'a': '26', 'b': '29', 'c': '56', 'd': '3', 'e': '24', 'f': '0', 'g': '47', 'h': '27', 'i': '22', 'j': '41',
        'k': '16', 'm': '11', 'n': '37', 'o': '2',
        'p': '35', 'q': '21', 'r': '17', 's': '33', 't': '30', 'u': '48', 'v': '23', 'w': '55', 'x': '32', 'y': '14',
        'z': '19'

    }
    # 2. 将key对应的value存入一个列表
    BvNo2: list[int] = []
    for index, ch in enumerate(BvNo1):
        BvNo2.append(int(str(keys[ch])))

    # 3. 对列表中不同位置的数进行*58的x次方的操作

    BvNo2[0]: int = int(BvNo2[0] * math.pow(58, 6))
    BvNo2[1]: int = int(BvNo2[1] * math.pow(58, 2))
    BvNo2[2]: int = int(BvNo2[2] * math.pow(58, 4))
    BvNo2[3]: int = int(BvNo2[3] * math.pow(58, 8))
    BvNo2[4]: int = int(BvNo2[4] * math.pow(58, 5))
    BvNo2[5]: int = int(BvNo2[5] * math.pow(58, 9))
    BvNo2[6]: int = int(BvNo2[6] * math.pow(58, 3))
    BvNo2[7]: int = int(BvNo2[7] * math.pow(58, 7))
    BvNo2[8]: int = int(BvNo2[8] * math.pow(58, 1))
    BvNo2[9]: int = int(BvNo2[9] * math.pow(58, 0))

    # 4.求出这10个数的合
    sum: int = 0
    for i in BvNo2:
        sum += i
    # 5. 将和减去100618342136696320
    sum -= 100618342136696320
    # 6. 将sum 与177451812进行异或
    temp: int = 177451812

    return sum ^ temp
"""

"""
async def get_top_comments(av: str) -> str:
    av: str = str(av)
    if av[0:2] == "BV":
        avcode = bv2av(av)
    else:
        avcode = av.replace("av", "")
    async with httpx.AsyncClient() as client:
        headers = {'Content-Type': "application/x-www-form-urlencoded"}
        r = await client.get(url=f'https://api.bilibili.com/x/v2/reply/main?next=0&type=1&oid={avcode}',
                             headers=headers)
    rd: dict[str:str, int, dict] = json.loads(r.text)
    if rd['code'] == "0":
        if not rd["data"]:
            return None
    hot_comments: dict[str:str, int, dict] = rd['data']['replies'][:3]
    msg: str = "\n-----------------\n--前三热评如下--\n-----------------\n"
    for c in hot_comments:
        name = c['member']['uname']
        txt = c['content']['message']
        msg += f'{name}: {txt}\n\n'
    return msg
"""

async def get_abv_data(abv_list: list[str]) -> list[str]:
    msg_list: list[str] = []
    for abvcode in abv_list:
        msg: str = ""
        abv_type = None  # None, "av", "bv"
        if abvcode[0:2].upper() == "BV":
            abv_type = "bv"
        elif abvcode[0:2].lower() == "av":
            abv_type = "av"
            abvcode = abvcode.replace("av", "")
        elif abvcode[0:7].lower() == "b23.tv/":
            # if b_b23tv:
            msg += abvcode + ", "
            abvcode = await b23tv2bv(abvcode)
            abv_type = "bv"
        else:
            continue
        new_url: str = url + (f"?bvid={abvcode}" if abv_type == "bv" else f"?aid={abvcode}")
        async with httpx.AsyncClient() as client:
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            r = await client.get(new_url, headers=headers)
        rd: dict[str:str, int, dict] = json.loads(r.text)
        if rd['code'] == 0:
            if not rd["data"]:
                continue
        else:
            continue
        if abv_type == "bv":
            msg += abvcode + "\n"
        else:
            msg += "av" + abvcode + "\n"
        try:
            title: str = rd['data']['title']
            pic: str = rd['data']['pic']
            stat: dict[str:str, int, dict] = rd['data']['stat']
            view: str = stat['view']
            danmaku: str = stat['danmaku']
            reply: str = stat['reply']
            fav: str = stat['favorite']
            coin: str = stat['coin']
            share: str = stat['share']
            like: str = stat['like']
            link: str = ""
            if abv_type == "bv":
                link: str = f"https://www.bilibili.com/video/{abvcode}"
            else:
                link: str = f"https://www.bilibili.com/video/av{abvcode}"
            desc: str = rd['data']['desc']
            if len(desc) > 32:
                desc = desc[0:32] + "……"

            msg += title + "\n" + MessageSegment.image(
                pic) + f"播放 {view} 弹幕 {danmaku} 评论 {reply}\n点赞 {like} 硬币 {coin} 收藏 {fav} 分享 {share}\n{link}\n简介\n{desc}"

            # if b_comments:
            #     msg += await get_top_comments(abvcode)

            msg_list.append(msg)
        except:
            msg += "错误!!! 没有此av或BV号。"

    return msg_list
