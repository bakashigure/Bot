import re
from collections import Counter

def get_status(date, group):
    print(date, group)
    log = rf"""{str(date)}-[0-9]*? .*? - __init__ - INFO - send message to
\[message.group.normal\]: Message -[0-9]*? from ([0-9]*?)@\[群:{str(group)}\]"""
    print(log)

    with open("../gpt.log") as f:
        data = f.read()
        s = re.findall(log, data)
        result = Counter(s)
    
    return result

