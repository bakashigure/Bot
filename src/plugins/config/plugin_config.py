import yaml
import time


class PluginConfig:

    def __init__(self, group_yaml_file, user_yaml_file):

        self.lock = False

        _prefix = './src/plugins/config/'
        self.group_yaml_path = _prefix + group_yaml_file
        self.user_yaml_path = _prefix + user_yaml_file

        """
        self.plugin_name_dict = {
            "plugin_name": (id, default_access),
            "plugin_name": (id, default_access),
            ...
        }
        """
        self.plugin_name_dict = {}

        """
        self.plugin_id_dict = {
            id: "plugin_name",
            id: "plugin_name",
            ...
        }
        """
        self.plugin_id_dict = {}

        """
        self.user_dict = {
            user: {
                "plugin_name": now_access,
                "plugin_name": now_access,
                ...
            },
            user: {
                "plugin_name": now_access,
                "plugin_name": now_access,
                ...
            },
            ...
        }
        """
        self.user_dict = dict()

        """
        self.group_dict = {
            group: {
                "plugin_name": now_access,
                "plugin_name": now_access,
                ...
            },
            group: {
                "plugin_name": now_access,
                "plugin_name": now_access,
                ...
            },
            ...
        }
        """
        self.group_dict = dict()

        # need to read again
        self.user_old = True
        self.group_old = True

        # need to write
        self.user_dirty = True
        self.group_dirty = True

    # should lock
    def register_plugins(self, plugin_name_dict) -> None:
        while self.lock:
            time.sleep(0.5)
        self.lock = True

        """
        [input]
        plugin_name_dict = {
            "plugin_name": (id, default_access),
            "plugin_name": (id, default_access),
            ...
        }
        """
        self.plugin_name_dict = plugin_name_dict
        self.plugin_id_dict = {tup[0] : name for (name, tup) in self.plugin_name_dict.items()}

        self.lock = False


    def get_name(self, id) -> str:
        return self.plugin_id_dict.get(id, None)


    def get_id(self, name) -> int:
        return self.plugin_name_dict.get(name, (None, False))[0]


    def get_default_access(self, name) -> int:
        return self.plugin_name_dict.get(name, (None, False))[1]


    def parse(self, id_or_name) -> tuple:
        """
        [input]
        id_or_name = str("name") or int(x)
        
        [output]
        tuple = (plugin_name, plugin_id, exist_flag)
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
            file = open(self.user_yaml_path, 'r', encoding='utf-8')
            yaml_read = yaml.safe_load(file.read())
            self.user_dict = {} if yaml_read is None else dict(yaml_read)
            file.close()
            self.user_old = False
        
        if self.group_old:
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
    
    def accessible(self, group_or_user_id: dict, plugin_name: str) -> bool:
        """
        [input]
        group_or_user_id = { "group": None, "user": 123456 }  or
                           { "group": 123456, "user": 123456 }  or
                           { "group": None, "user": None }
        """
        self.read()
        pid = self.get_id(plugin_name)
        if pid is None:
            return
        if group_or_user_id["group"] != None:
            return self.group_dict.get(group_or_user_id["group"], {}).get(
                plugin_name, self.get_default_access(plugin_name)
            )
        elif group_or_user_id["user"] != None:
            return self.user_dict.get(group_or_user_id["user"], {}).get(
                plugin_name, self.get_default_access(plugin_name)
            )
        return False

    # should lock internal
    def change_access(self, group_or_user_id: dict, plugin_name: str, access: bool) -> None:

        """
        [input]
        group_or_user_id = { "group": None, "user": 123456 }  or
                           { "group": 123456, "user": 123456 }  or
                           { "group": None, "user": None }
        """
        self.read()
        pid = self.get_id(plugin_name)
        if pid is None:
            return
        
        while self.lock:
            time.sleep(0.5)
        self.lock = True

        if group_or_user_id["group"] != None:
            self.group_dict.setdefault(group_or_user_id["group"], {})[plugin_name] = access
            self.group_dirty = True
        elif group_or_user_id["user"] != None:
            self.user_dict.setdefault(group_or_user_id["user"], {})[plugin_name] = access
            self.user_dirty = True
        
        self.lock = False

        self.write()

    def show(self, option: str = None, search_id: int = None) -> str:
        """
        option: None, 'None', 'group', 'g', 'user', 'u'
        """
        self.read()
        res = ""
        if option is None or option == 'None' or option in ['user', 'u']:
            res += "[user_dict]\n"
            if search_id is not None:
                for user_dicts in self.user_dict.items():
                    if user_dicts[0] == search_id:
                        res += yaml.dump({user_dicts[0]: user_dicts[1]}, allow_unicode=True) + "\n"
            else:
                res += yaml.dump(self.user_dict, allow_unicode=True) + "\n"
        if option is None or option == 'None' or option in ['group', 'g']:
            res += "[group_dict]\n"
            if search_id is not None:
                for group_dicts in self.group_dict.items():
                    if group_dicts[0] == search_id:
                        res += yaml.dump({group_dicts[0]: group_dicts[1]}, allow_unicode=True) + "\n"
            else:
                res += yaml.dump(self.group_dict, allow_unicode=True) + "\n"
        return res


"""
plugin_name 是唯一标识符，必须和你的插件文件夹名一致
plugin_id 仅仅是面向用户的时候方便处理而造的，只要不重就行
"""


# non-hidden:
# only group owner / admin & superuser can change permission for group
# user can only use the default access, unless mannual granted in yaml file
# name, id cannot be the same (cannot be the same as hidden, neither)

plugin_config = PluginConfig(
    'group_config.yaml',
    'user_config.yaml'
)
plugin_config.register_plugins({
    "help": (1, True),
    "echo": (2, True),
    "random": (3, True),

    # "背日语": (65, False),
    # "搜图": (66, False),
    # "翻译": (67, True),
    "缩写": (68, True),
    # "Arcaea": (69, True),
})



# hidden:
# only superuser can change permission for group
# user can only use the default access, unless mannual granted in yaml file
# name, id cannot be the same (cannot be the same as non-hidden, neither)

hidden_plugin_config = PluginConfig(
    'group_hidden_config.yaml',
    'user_hidden_config.yaml'
)
hidden_plugin_config.register_plugins({
    "戳一戳": (-1, True),
    "青年大学习": (-2, False),
    "疫情填报": (-3, False),
})



# all
all_plugin_config_list = [
    plugin_config,
    hidden_plugin_config,
]