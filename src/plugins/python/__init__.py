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

def signal_handler(signum, frame):
    raise Exception("Timed out!")

# your_plugin_catcher = on_message(rule=startswith(("", "")))
python_catcher = on_regex(r"^(?:python\r?\n)((?:.|\s)*?)$")

@python_catcher.handle()
async def _(bot: Bot, event: Event):
    raw_msg = str(event.get_message())
    # event_dict = event.dict()
    # group_id = event_dict.get('group_id', 0)
    # raw_msg = event_dict['raw_message']
    content = re.findall(r"^(?:python\r?\n)((?:.|\s)*?)$", raw_msg)[0]
    content = content.replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')
    for i in ['dir', 'bin', 'exec', 'nonebot', 'sys', 'subprocess', 'os', 'shutil', 'winreg', 'open', 'write']:
        if i in content:
            await python_catcher.send('暂不可执行该内容')
            return
    # old_stdout = sys.stdout
    # signal.signal(signal.SIGALRM, signal_handler)
    # signal.alarm(5)
    try:
        # redirected_output = sys.stdout = StringIO()
        with open('./tmp.py', 'w+') as f:
            f.write(content)
        p = subprocess.run(["python3", "./tmp.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", timeout=5)
        res = p.stdout.rstrip()
        res = res.replace('/home/ubuntu/bot/sweetbot', '/tmp').replace('/home/ubuntu/miniconda3/envs/bot', '/tmp/conda/envs/tmp')
        if res is not None and res != '':
            await python_catcher.send(res)
        # func_timeout.func_timeout(5, exec, args=(str(content), dict(locals())))
        # sys.stdout = old_stdout
        # await python_catcher.send(redirected_output.getvalue())
    except subprocess.TimeoutExpired:
        await python_catcher.send('TimeOutError')
    except Exception as e:
        await python_catcher.send(str(e))
    await python_catcher.finish()
