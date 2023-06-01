import re
import yaml
from typing import Optional, Union, Tuple, List

# this is use to replace re.findall() with ',', '.', ';', ...
def parse(
        raw_message: str,
        head: Optional[Union[str, Tuple[str, ...], List[str]]] = None,
        strict: bool = False
) -> Optional[list]:
    loose_split_list = [
        ' ', '　', '\t', '\n', '\r',
        '.', '。',
        ',', '，', '、',
        ':', '：',
        ';', '；'
    ]

    strict_split_list = [
        ' ', '\t', '\n', '\r',
    ]

    res = []
    temp = ""

    split_list = loose_split_list
    if strict:
        split_list = strict_split_list

    raw_message = raw_message.strip()
    if head is not None:
        if not raw_message.startswith(head):
            return
        if type(head) is not str:
            pattern = re.compile(r"^({})".format("|".join(head)))
            real_head = re.findall(pattern, raw_message)[0]
            raw_message = raw_message.removeprefix(real_head)
            res.append(real_head)
        else:
            raw_message = raw_message.removeprefix(head)
            res.append(head)

    for i in raw_message:
        if i in split_list:
            if temp != "":
                res.append(temp)
                temp = ""
        else:
            temp = temp + i
    if temp != "":
        res.append(temp)
    return res