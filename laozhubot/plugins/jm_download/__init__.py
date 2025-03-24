from nonebot import on_command,logger,get_plugin_config
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .config import Config

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

jm_download = on_command('jm下载',rule=to_me(),aliases={"jm", "本子下载"}, priority=5, block=True)

@jm_download.handle()
async def handle_download_function(args: Message = CommandArg()):
    if num := args.extract_plain_text():
        await jm_download.send(f"开始下载{num}")
    else:
        await jm_download.finish("未输入编号")
    import jmcomic
