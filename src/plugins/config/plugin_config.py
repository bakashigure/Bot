import os
import yaml
import time
import json
from typing import Tuple
from pathlib import Path


class PluginConfig:

    def __init__(self, file_dir_path, group_yaml_file, user_yaml_file):

        self.lock = False
        self.group_yaml_path = Path(file_dir_path) / Path(group_yaml_file)
        self.user_yaml_path = Path(file_dir_path) / Path(user_yaml_file)

        self.plugin_name_dict = {}
        """
        self.plugin_name_dict = {
            "plugin_name": [id, default_access],
            "plugin_name": [id, default_access],
            ...
        }\n
        `id` is int32 number\n
        `default_access` is true or false
        """

        self.plugin_id_dict = {}
        """
        self.plugin_id_dict = {
            id: "plugin_name",
            id: "plugin_name",
            ...
        }\n
        `id` is int32 number
        """

        self.user_dict = dict()
        """
        self.user_dict = {
            user_id: {
                "plugin_name": "<now_access>",
                "plugin_name": "<now_access>",
                ...
            },
            user_id: {
                "plugin_name": "<now_access>",
                "plugin_name": "<now_access>",
                ...
            },
            ...
        }\n
        "<now_access>" is "t" (true), "f" (false) or "d" (default)
        """

        self.group_dict = dict()
        """
        self.group_dict = {
            group_id: {
                "plugin_name": "<now_access>",
                "plugin_name": "<now_access>",
                ...
            },
            group_id: {
                "plugin_name": "<now_access>",
                "plugin_name": "<now_access>",
                ...
            },
            ...
        }\n
        "<now_access>" is "t" (true), "f" (false) or "d" (default)
        """

        # need to read again
        self.user_old = True
        self.group_old = True

        # need to write
        self.user_dirty = True
        self.group_dirty = True

    # should lock
    def register_plugins(self, plugin_name_dict: dict) -> None:
        """
        plugin_name_dict:
            ```python
            {
                "plugin_name": [id, default_access],
                "plugin_name": [id, default_access],
                ...
            }
            ```
            `id` is an int32 number, `default_access` is `True` or `False`
        """
        while self.lock:
            time.sleep(0.5)
        self.lock = True
        self.plugin_name_dict = plugin_name_dict
        self.plugin_id_dict = {tup[0] : name for (name, tup) in self.plugin_name_dict.items()}
        self.lock = False


    def get_name(self, id: int) -> str:
        return self.plugin_id_dict.get(id, None)


    def get_id(self, name: str) -> int:
        return self.plugin_name_dict.get(name, (None, False))[0]


    def get_default_access(self, name: str) -> int:
        return self.plugin_name_dict.get(name, (None, False))[1]


    def parse(self, id_or_name) -> Tuple[str, int, bool]:
        """
        id_or_name: str("name") or int(x)
        return: (plugin_name, plugin_id, exist_flag)
        """
        pid, name = None, None
        if id_or_name.isdigit() or (id_or_name[0] == '-' and id_or_name[1:].isdigit()):
            pid = int(id_or_name)
            name = self.get_name(pid)
        else:
            name = id_or_name
            pid = self.get_id(name)
        if name is None or pid is None:
            return name, pid, False
        return name, pid, True

    def items(self):
        return self.plugin_id_dict.items()

    # should lock
    def read(self) -> None:
        while self.lock:
            time.sleep(0.5)
        self.lock = True

        if self.user_old:
            if not os.path.exists(self.user_yaml_path):
                open(self.user_yaml_path, 'w', encoding='utf-8').close()
            file = open(self.user_yaml_path, 'r', encoding='utf-8')
            yaml_read = yaml.safe_load(file.read())
            self.user_dict = {} if yaml_read is None else dict(yaml_read)
            file.close()
            self.user_old = False
        
        if self.group_old:
            if not os.path.exists(self.group_yaml_path):
                open(self.group_yaml_path, 'w', encoding='utf-8').close()
            file = open(self.group_yaml_path, 'r', encoding='utf-8')
            yaml_read = yaml.safe_load(file.read())
            self.group_dict = {} if yaml_read is None else dict(yaml_read)
            file.close()
            self.group_old = False
        
        self.lock = False

    # should lock
    def write(self) -> None:
        while self.lock:
            time.sleep(0.5)
        self.lock = True

        if self.user_dirty:
            file = open(self.user_yaml_path, 'w', encoding='utf-8')
            yaml.dump(self.user_dict, file, allow_unicode=True)
            file.close()
            self.user_dirty = False

        if self.group_dirty:
            file = open(self.group_yaml_path, 'w', encoding='utf-8')
            yaml.dump(self.group_dict, file, allow_unicode=True)
            file.close()
            self.group_dirty = False
        
        self.lock = False
    
    def accessible(self, group_or_user_dict: dict, plugin_name: str) -> Tuple[bool, bool]:
        """
        group_or_user_dict:
            ```python
            { "group": None, "user": '123456' } or { "user": 123456 }  # detect user
            { "group": 123456, "user": None } or { "group": '123456', "user": 123456 } or { "group": 123456 }  # detect group
            { "group": None, "user": None }  # return False, False
            ```
        return: (accessible(True of False), is_default(True of False))
        """
        self.read()
        pid = self.get_id(plugin_name)
        if pid is None:
            return (False, False)
        
        def str_to_tf(input_str: str):
            if input_str == "t":
                return True
            elif input_str == "f":
                return False
            else:
                return "d"

        if group_or_user_dict.get("group", None) != None:
            result = str_to_tf(
                self.group_dict.get(int(group_or_user_dict["group"]), {}).get(plugin_name, "d")
            )
            if result == "d":
                return (self.get_default_access(plugin_name), True)
            else:
                return (result, False)
        elif group_or_user_dict.get("user", None) != None:
            result = str_to_tf(
                self.user_dict.get(int(group_or_user_dict["user"]), {}).get(plugin_name, "d")
            )
            if result == "d":
                return (self.get_default_access(plugin_name), True)
            else:
                return (result, False)
        else:
            return (False, False)

    # should lock internal
    def change_access(self, group_or_user_dict: dict, plugin_name: str, access: str = "d") -> None:

        """
        group_or_user_dict:
            ```python
            { "group": None, "user": '123456' } or { "user": 123456 }  # detect user
            { "group": 123456, "user": None } or { "group": '123456', "user": 123456 } or { "group": 123456 }  # detect group
            { "group": None, "user": None }  # do nothing
            ```
        access: `"t"`, `"true"`, `True`, `"f"`, `"false"`, `False`, `"d"`, `"default"`
        """
        self.read()
        pid = self.get_id(plugin_name)
        if pid is None:
            return
        
        while self.lock:
            time.sleep(0.5)
        self.lock = True

        access_data = "d"
        if access in ["d", "default"]:
            access_data = "d"
        elif access in ["t", "true", True]:
            access_data = "t"
        elif access in ["f", "false", False]:
            access_data = "f"

        if group_or_user_dict.get("group", None) != None:
            id = int(group_or_user_dict["group"])
            if access_data == "d":
                self.group_dict.setdefault(id, {}).pop(plugin_name, None)
            else:
                self.group_dict.setdefault(id, {})[plugin_name] = access_data
            self.group_dirty = True
        elif group_or_user_dict.get("user", None) != None:
            id = int(group_or_user_dict["user"])
            if access_data == "d":
                self.user_dict.setdefault(id, {}).pop(plugin_name, None)
            else:
                self.user_dict.setdefault(id, {})[plugin_name] = access_data
            self.user_dirty = True

        self.lock = False

        self.write()

    def show(self, option: str = 'all', search_id: int | str = None) -> str:
        """
        option: `'all'`, `'a'`, `'group'`, `'g'`, `'user'`, `'u'`
        search_id: if is None, only show those have been edited
        """
        self.read()
        res = ""
        if option in ['all', 'a', 'user', 'u']:
            if option in ['all', 'a']:
                res += "[user_dict]\n"

            # show a single id, so all default must be shown
            if search_id is not None:
                search_id = int(search_id)
                shown = False
                for user_dicts in self.user_dict.items():
                    if user_dicts[0] == search_id:
                        res += f"user {search_id}:\n"
                        for (plugin_name, id_and_access) in self.plugin_name_dict.items():
                            res += f"\t{plugin_name} ({id_and_access[0]}): "
                            accessible_and_default = self.accessible({"user": search_id}, plugin_name)
                            if accessible_and_default[1] is True:
                                res += f"{accessible_and_default[0]} (default)\n"
                            else:
                                res += f"{accessible_and_default[0]}\n"
                        res += "\n"
                        shown = True
                        break
                if not shown:
                    res += f"user {search_id} (ALL DEFAULT):\n"
                    for (plugin_name, id_and_access) in self.plugin_name_dict.items():
                        res += f"\t{plugin_name} ({id_and_access[0]}): "
                        accessible_and_default = self.accessible({"user": search_id}, plugin_name)
                        # must be default
                        res += f"{accessible_and_default[0]} (default)\n"
                    res += "\n"
                    shown = True

            # show all edited, default ignored
            else:
                for user_dicts in self.user_dict.items():
                    res += f"user {user_dicts[0]}:\n"
                    for (plugin_name, id_and_access) in self.plugin_name_dict.items():
                        res += f"\t{plugin_name} ({id_and_access[0]}): "
                        accessible_and_default = self.accessible({"user": user_dicts[0]}, plugin_name)
                        if accessible_and_default[1] is True:
                            res += f"{accessible_and_default[0]} (default)\n"
                        else:
                            res += f"{accessible_and_default[0]}\n"
                    res += "\n"

        if option in ['all', 'a', 'group', 'g']:
            if option in ['all', 'a']:
                res += "[group_dict]\n"
            
            # show a single id, so all default must be shown
            if search_id is not None:
                search_id = int(search_id)
                shown = False
                for group_dicts in self.group_dict.items():
                    if group_dicts[0] == search_id:
                        res += f"group {search_id}:\n"
                        for (plugin_name, id_and_access) in self.plugin_name_dict.items():
                            res += f"\t{plugin_name} ({id_and_access[0]}): "
                            accessible_and_default = self.accessible({"group": search_id}, plugin_name)
                            if accessible_and_default[1] is True:
                                res += f"{accessible_and_default[0]} (default)\n"
                            else:
                                res += f"{accessible_and_default[0]}\n"
                        res += "\n"
                        shown = True
                        break
                if not shown:
                    res += f"group {search_id} (ALL DEFAULT):\n"
                    for (plugin_name, id_and_access) in self.plugin_name_dict.items():
                        res += f"\t{plugin_name} ({id_and_access[0]}): "
                        accessible_and_default = self.accessible({"group": search_id}, plugin_name)
                        # must be default
                        res += f"{accessible_and_default[0]} (default)\n"
                    res += "\n"
                    shown = True

            # show all edited
            else:
                for group_dicts in self.group_dict.items():
                    res += f"group {group_dicts[0]}:\n"
                    for (plugin_name, id_and_access) in self.plugin_name_dict.items():
                        res += f"\t{plugin_name} ({id_and_access[0]}): "
                        accessible_and_default = self.accessible({"group": group_dicts[0]}, plugin_name)
                        if accessible_and_default[1] is True:
                            res += f"{accessible_and_default[0]} (default)\n"
                        else:
                            res += f"{accessible_and_default[0]}\n"
                    res += "\n"

        return res

"""
所有配置都在 plugin.json 中
"""

with open('./src/plugins/config/plugin.json', 'r') as plugin_file:
    plugin_data = json.load(plugin_file)

    # non-hidden:
    # only group owner / admin & superuser can change permission for group
    # user can only use the default access, unless mannual granted in yaml file
    # name, id cannot be the same (cannot be the same as hidden, neither)

    normal_plugins = PluginConfig(
        plugin_data["file_dir_path"],
        plugin_data["normal"]["file"]["group"],
        plugin_data["normal"]["file"]["user"],
    )
    normal_plugins.register_plugins(plugin_data["normal"]["register"])

    # hidden:
    # only superuser can change permission for group
    # user can only use the default access, unless mannual granted in yaml file
    # name, id cannot be the same (cannot be the same as non-hidden, neither)

    hidden_plugins = PluginConfig(
        plugin_data["file_dir_path"],
        plugin_data["hidden"]["file"]["group"],
        plugin_data["hidden"]["file"]["user"],
    )
    hidden_plugins.register_plugins(plugin_data["hidden"]["register"])

    # all
    all_plugins_lists = [
        normal_plugins,
        hidden_plugins,
    ]
