import contextlib
from re import I

from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from laozhubot.plugins.setu import manager_handle
from laozhubot.plugins.setu.send_setu import send_setu

with contextlib.suppress(Exception):
    # 用于在 with 语句块中 静默（即不抛出）指定的异常
    __plugin_meta__ = PluginMetadata(
        name='laozhu_setu',
        description='老猪机器人涩图插件',
        usage=r'^(setu|色图|涩图|想色色|来份色色|来份色图|想涩涩|多来点|来点色图|来张setu|来张色图|来点色色|色色|涩涩)\s?([x|✖️|×|X|*]?\d+[张|个|份]?)?\s?(r18)?\s?(.*)?',
        type='application',
        homepage="https://github.com/LaoZhuJackson/lzbot.git",
        supported_adapters={"~onebot.v11"},
        extra={
            "author": "laozhu",
            "version": "0.1.0",
            "priority": 10,
        },
    )

# 命令正则表达式
setu_regex: str = r"^(setu|色图|涩图|想色色|来份色色|来份色图|想涩涩|多来点|来点色图|来张setu|来张色图|来点色色|色色|涩涩)\s?([x|✖️|×|X|*]?\d+[张|个|份]?)?\s?(r18)?\s?(.*)?"
# on_regex 是 Nonebot 提供的装饰器，用于监听匹配特定正则表达式的消息。它会在收到符合正则表达式的消息时触发一个对应的事件处理器。
on_regex(
    setu_regex,
    # flags 是正则表达式的标志，这里 I 是正则表达式中的 re.IGNORECASE 标志，意味着匹配时不区分大小写。也就是说，setu_regex 可以匹配 setu、Setu、SETU 等不同大小写的字符串。
    flags=I,
    # priority 表示事件处理器的优先级。优先级较高的事件处理器会先被执行。
    priority=20,
    # block 表示是否阻止其他处理器的执行。如果设置为 True，一旦这个处理器被触发，其他相同类型的处理器就不会再执行。
    block=True,
    # handlers 是一个列表，其中包含处理该事件的函数。
    handlers=[send_setu.setu_handle],
)

# ----- 白名单添加与解除 -----
on_command(
    "setu_wl",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.open_setu],
)


# ----- r18添加与解除 -----
on_command(
    "setu_r18",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.set_r18],
)


# ----- cd时间更新 -----
on_command(
    "setu_cd",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.set_cd],
)


# ----- 撤回时间更新 -----
on_command(
    "setu_wd",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.set_wd],
)


# ----- 最大张数更新 -----
on_command(
    "setu_mn",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.set_maxnum],
)


# ----- 黑名单添加与解除 -----
on_command(
    "setu_ban",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.ban_setu],
)


# --------------- 发送帮助信息 ---------------
on_command(
    "setu_help",
    block=True,
    priority=10,
    aliases={"setu_帮助", "色图_help", "色图_帮助"},
    handlers=[manager_handle.setu_help],
)


# --------------- 更换代理 ---------------
on_command(
    "更换代理",
    block=True,
    priority=10,
    permission=SUPERUSER,
    aliases={"替换代理", "setu_proxy"},
    handlers=[manager_handle.replace_proxy, manager_handle.replace_proxy_got],
)


# --------------- 查询黑白名单 ---------------
on_command(
    "setu_roster",
    block=True,
    priority=10,
    aliases={"色图名单"},
    permission=SUPERUSER,
    handlers=[manager_handle.query_black_white_list],
)


# --------------- 数据库更新 ---------------
on_command(
    "setu_db",
    block=True,
    priority=10,
    permission=SUPERUSER,
    handlers=[manager_handle.setu_db],
)
