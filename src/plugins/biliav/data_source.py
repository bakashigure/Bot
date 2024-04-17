import re
import json
import httpx
import traceback

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .bililogger import bililogger


HEADER = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "image/gif, image/jpeg, image/pjpeg, application/x-ms-application, application/xaml+xml, application/x-ms-xbap, */*",
    "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; Tablet PC 2.0; wbx 1.0.0; wbxapp 1.0.0; Zoom 3.6.0)"
}

async def b23tv2bv(b23tv: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get('https://' + b23tv, headers=HEADER)
    return re.findall("[Bb][Vv]1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2}", str(r.next_request.url))[0]


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
    video_list = set()

    URL: str = 'https://api.bilibili.com/x/web-interface/view'

    if len(abv_list) == 0:
        bililogger.warning("no abv_list")

    for abvcode in abv_list:

        # get real av / bv
        abv_type = "av"
        if abvcode[0:2].lower() == "bv":
            abv_type = "bv"
            bililogger.info(f"deal with bv: {abvcode}")
        elif abvcode[0:2].lower() == "av":
            abv_type = "av"
            abvcode = abvcode.replace("av", "")
            bililogger.info(f"deal with av: {abvcode}")
        elif abvcode[0:7].lower() == "b23.tv/":
            # if b_b23tv:
            abvcode = await b23tv2bv(abvcode)
            abv_type = "bv"
            bililogger.info(f"deal with bv from btv: {abvcode}")
        else:
            bililogger.error(f"deal abv error: {abvcode}")
            continue

        # delete duplicated
        if abvcode in video_list:
            bililogger.warning(f"abvcode {abvcode} detected before, skipping")
            continue

        # get the data
        new_url: str = URL + (f"?bvid={abvcode}" if abv_type == "bv" else f"?aid={abvcode}")
        bililogger.info(f"start to request {new_url}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(new_url, headers=HEADER)
            rd: dict[str:str, int, dict] = json.loads(r.text)
        except Exception as e:
            bililogger.error(str(e))
            bililogger.error(str(traceback.format_exc()))
            continue

        # if error
        if rd['code'] == 0 and not rd["data"]:
            bililogger.error('get rd["data"] error')
            continue
        elif rd['code'] != 0:
            bililogger.error(f'get rd["code"] error: {rd["code"]}')
            continue

        # av code change
        if abv_type == "av":
            abvcode = "av" + abvcode

        # succeed
        try:
            title: str = rd['data']['title']
            author: str = rd['data'].get('owner').get('name')
            pic: str = rd['data']['pic']
            stat: dict[str:str, int, dict] = rd['data']['stat']
            view: str = stat['view']
            danmaku: str = stat['danmaku']
            reply: str = stat['reply']
            fav: str = stat['favorite']
            coin: str = stat['coin']
            share: str = stat['share']
            like: str = stat['like']
            link: str = f"https://www.bilibili.com/video/{abvcode}"
            desc: str = rd['data']['desc']
            if len(desc) > 32: desc = desc[0:32] + "……"

            msg = f"{title}\n{author}\n" \
                + MessageSegment.image(pic) \
                + f"播放 {view} 弹幕 {danmaku} 评论 {reply}\n点赞 {like} 硬币 {coin} 收藏 {fav} 分享 {share}\n{link}\n简介\n{desc}"
            msg_list.append(msg)

            # delete duplicated
            video_list.add(abvcode[2:] if abv_type == "av" else abvcode)

            bililogger.info(f"send messsage (short)\n{title=}\n{author=}\n{pic=}")

        except Exception as e:
            bililogger.error(e)
            bililogger.error(str(traceback.format_exc()))
            continue

    return msg_list
