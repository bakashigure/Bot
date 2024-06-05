import pathlib
import random

def get_random(context_file_name):

    context_file = pathlib.Path(context_file_name)

    start = "#start"
    end = "#end"

    # choose max to 11 candidates: first valid, 10 below
    # prefer candidate: from tail to head
    ran_list = []
    for i in range(0, 10):
        ran_list.append(random.randint(0, 2 ** i))
    choose_list = []

    with open(context_file, "r", encoding='utf-8') as f:

        lines = f.readlines()

        line_buff = 0
        context_buff = ""
        is_first = True
        now_num = 0
        not_occupied = True
        valid_context = False

        for line_number, line in enumerate(lines): 
            line = line.strip()
            if line == "": line = "\n"
            if not valid_context:
                if line.startswith(start):
                    line_buff = line_number
                    valid_context = True
                    if line.endswith("<USED>"):
                        not_occupied = False
            else:
                if line.startswith(end):
                    if not_occupied and (is_first or now_num in ran_list):
                        choose_list.append((line_buff, context_buff))
                        context_buff = ""
                        is_first = False
                    valid_context = False
                    not_occupied = True
                    now_num += 1
                elif not_occupied:
                    if is_first or now_num in ran_list:
                        context_buff += line
    
    if len(choose_list) == 0:
        return ""
    
    choose_list.reverse()
    line_to_modify, data = choose_list[0]

    lines[line_to_modify] = lines[line_to_modify].rstrip() + ' <USED>\n'
    with open(context_file, 'w', encoding='utf-8') as file:
        file.writelines(lines)

    return data

