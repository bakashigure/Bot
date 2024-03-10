import re
from nonebot.log import logger
from nonebot.rule import startswith
from nonebot import on_message, on_regex
from nonebot.adapters.onebot.v11 import Bot, Event

import time
import sys
import signal
import subprocess
from io import StringIO

from .pythonlogger import pylogger

def signal_handler(signum, frame):
    raise Exception("Timed out!")

# your_plugin_catcher = on_message(rule=startswith(("", "")))
python_catcher = on_regex(r"^(?:python\r?\n)((?:.|\s)*?)$")

@python_catcher.handle()
async def _(bot: Bot, event: Event):

    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', 0)
    # raw_msg = event_dict['raw_message']

    raw_msg = str(event.get_message())
    pylogger.debug(event.get_log_string())
    content: str = re.findall(r"^(?:python\r?\n)((?:.|\s)*?)$", raw_msg)[0]
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')

    start_import = []
    SAFE_IMPORT = ['import math', 'import random', 'import numpy', 'import numpy as np', 'import time']
    test = re.findall(r'((?:import|from)[\s]*.*?)(?:\r?\n|$|;)', content)
    pylogger.warn(test)
    for i in test:
        if i in SAFE_IMPORT:
            start_import.append(i + '\n')
            content = content.replace(i, '')

    for i in ['import', '__import__', '__builtins__', '__class__', 'open', 'write', 'save', "load", "dump", "file", 'dir', 'eval', 'exec', 'commands', 'pty', 'subprocess', 'sys', 'os', 'shutil', 'winreg', 'fileinput', 'glob', 'nonebot']:
        re_pattern_str = rf'(?:^|[^a-zA-Z0-9])({i})(?:$|[^a-zA-Z0-9])'
        matched = re.findall(re_pattern_str, content)
        if len(matched) > 0:
            pylogger.error(matched)
            await python_catcher.send('暂不可执行该内容')
            return

    try:
        with open('./tmp.py', 'w+') as f:
            f.writelines(start_import)
            f.write(content)
        p = subprocess.run(["python3", "./tmp.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", timeout=5)
        res = p.stdout.rstrip()
        res = res.replace('/home/ubuntu/bot/sweetbot', '/tmp').replace('/home/ubuntu/miniconda3/envs/bot', '/tmp/conda/envs/tmp')
        if res is not None and res != '':
            pylogger.info(res)
            await python_catcher.send(res)
        else:
            pylogger.error('None')
    except subprocess.TimeoutExpired:
        pylogger.error('TimeOutError')
        await python_catcher.send('TimeOutError')
    except Exception as e:
        pylogger.error(str(e))
        await python_catcher.send(str(e))
    await python_catcher.finish()
