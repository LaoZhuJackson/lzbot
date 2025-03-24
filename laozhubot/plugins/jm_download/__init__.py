from nonebot import on_command, logger, get_plugin_config
from nonebot.adapters.onebot.v12 import MessageSegment
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg, Command
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11.helpers import (
    Cooldown,
    CooldownIsolateLevel,
    autorevoke_send,
    Bot,
    Event
)
from nonebot.adapters.onebot.v11.event import NoticeEvent, MessageEvent, GroupMessageEvent,Event, GroupUploadNoticeEvent
from pathlib import Path
from nonebot.permission import SUPERUSER
from .config import Config
from .utils import structure_node

# __plugin_meta__ = PluginMetadata(
#     name="jm下载",
#     description="自动下载jm指定本子，并转换成pdf上传",
#     usage="/jm下载 XXXX",
#     type="application",  # library
#     homepage="",
#     config=Config,
#     supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna", "nonebot_plugin_uninfo"),
#     # supported_adapters={"~onebot.v11"},
#     extra={"author": "laozhu"},
# )

plugin_config = get_plugin_config(Config)

jm_enable = on_command('开启jm', rule=to_me(), aliases={'关闭jm'}, permission=SUPERUSER)


@jm_enable.handle()
async def set_enable(cmd: str = Command()):
    if '开启' in cmd:
        plugin_config.jm_enable = True
    elif '关闭' in cmd:
        plugin_config.jm_enable = False
    await jm_enable.finish(f'已{cmd}')


async def is_enable():
    return plugin_config.jm_enable


jm_download = on_command('jm下载', rule=is_enable, aliases={"jm", "本子下载"}, priority=5, block=True)


@jm_download.handle(
    parameterless=[
        Cooldown(cooldown=plugin_config.jm_personal_cd, prompt="冲太快了，去找卵龙导一发后再试",
                 isolate_level=CooldownIsolateLevel.USER)]
)
async def handle_download_function(bot: Bot, event: Event, args: Message = CommandArg()):
    if num := args.extract_plain_text():
        import jmcomic
        option = jmcomic.create_option_by_file('/home/laozhu/lzbot/laozhubot/plugins/jm_download/option.yml')
        try:
            jmcomic.download_album(num, option)
            await jm_download.send(f"下载{num}完成")
        except Exception as e:
            await jm_download.finish(f"下载{num}失败: {e}")

        pdf_path = Path('/home/laozhu/lzbot/data/jm/pdf')

        # 检查文件夹是否存在
        if not pdf_path.exists() or not pdf_path.is_dir():
            await jm_download.finish("PDF文件夹不存在")

        # 构建完整文件路径
        pdf_file = pdf_path / f"{num}.pdf"

        # 检查文件是否存在
        if not pdf_file.exists():
            await jm_download.finish(f"找不到PDF文件: {num}.pdf")

        # 发送文件（适配器相关部分）
        try:
            message = MessageSegment.file(str(pdf_file))
            await jm_download.finish(message)
        except Exception as e:
            await jm_download.finish(f"发送PDF文件失败: {e}")
    else:
        await jm_download.finish("未输入编号")
