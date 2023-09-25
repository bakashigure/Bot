# plugin: authority and help

这似乎也是一个插件，但是和其他插件有什么不同呢？

和其他插件：authority_help 无法关闭，且不会在功能栏中显示出来，它是控制插件服务的一个插件。  
authority_help 利用 `config/` 的 plugin_config 开关权限。

## 保留使用（不建议作为插件名，否则没法开关）

隐藏触发关键词：(隐藏)(...|功能|内容|插件)  
全选关键词：(全部|所有)(...|功能|内容|插件)

## appendix

event.dict()

group: {
    'time': 1600000000,
    'self_id': 123456789,
    'post_type': 'message',
    'sub_type': 'normal',
    'user_id': 1234567,
    'message_type': 'group',
    'message_id': -1479544568,  # ?
    'message': [MessageSegment(type='text', data={'text': '你好'})],  # 感觉不如 raw_message
    'original_message': [MessageSegment(type='text', data={'text': '你好'})],  # 感觉不如 raw_message
    'raw_message': '你好',
    'font': 0,  # ?
    'sender': {'user_id': 1234567, 'nickname': 'QAQ', 'sex': 'unknown', 'age': 0, 'card': '', 'area': '', 'level': '', 'role': 'owner', 'title': ''}, 'to_me': False,
    'reply': None,
    'group_id': 12345678,
    'anonymous': None,
    'message_seq': 7442  # ?
}