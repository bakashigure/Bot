import re
import sys
import json
import httpx
import logging
# from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment


logger = logging.getLogger("biliav")
logger.setLevel(logging.DEBUG)
logger.propagate = False

hfh_formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
)
hfh = logging.handlers.RotatingFileHandler(
    '../biliav.log', mode="a", maxBytes=1024 * 1024 * 8, backupCount=1
)
hfh.setFormatter(hfh_formatter)
logger.addHandler(hfh)

hsh_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(module)s | %(message)s"
)
hsh = logging.StreamHandler(sys.stdout)
hsh.setFormatter(hsh_formatter)
logger.addHandler(hsh)


HEADER = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "image/gif, image/jpeg, image/pjpeg, application/x-ms-application, application/xaml+xml, application/x-ms-xbap, */*",
    "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; Tablet PC 2.0; wbx 1.0.0; wbxapp 1.0.0; Zoom 3.6.0)"
}

async def b23tv2bv(b23tv: str) -> str:
    async with httpx.AsyncClient() as client:
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
        logger.warning("no abv_list")

    for abvcode in abv_list:

        # get real av / bv
        abv_type = "av"
        if abvcode[0:2].lower() == "bv":
            abv_type = "bv"
            logger.debug("bv")
        elif abvcode[0:2].lower() == "av":
            abv_type = "av"
            abvcode = abvcode.replace("av", "")
            logger.debug("av")
        elif abvcode[0:7].lower() == "b23.tv/":
            # if b_b23tv:
            abvcode = await b23tv2bv(abvcode)
            abv_type = "bv"
            logger.debug("bv (from btv)")
        else:
            logger.error("detect av or bv error")
            continue

        # delete duplicated
        if abvcode in video_list:
            logger.warning(f"abvcode {abvcode} detected, skipping")
            continue

        # get the data
        new_url: str = URL + (f"?bvid={abvcode}" if abv_type == "bv" else f"?aid={abvcode}")
        logger.warning(f"start to request {new_url}")
        async with httpx.AsyncClient() as client:
            r = await client.get(new_url, headers=HEADER)
        rd: dict[str:str, int, dict] = json.loads(r.text)

        # if error
        if rd['code'] == 0 and not rd["data"]:
            logger.error('get rd["data"] error')
            continue
        elif rd['code'] != 0:
            logger.error(f'get rd["code"] error, {rd["code"]}')
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

            logger.info(f"titled {title}")
            msg = f"{title}\n{author}\n" \
                + MessageSegment.image(pic) \
                + f"播放 {view} 弹幕 {danmaku} 评论 {reply}\n点赞 {like} 硬币 {coin} 收藏 {fav} 分享 {share}\n{link}\n简介\n{desc}"
            msg_list.append(msg)

            # delete duplicated
            video_list.add(abvcode[2:] if abv_type == "av" else abvcode)

        except Exception as e:
            logger.error(e)

    return msg_list
