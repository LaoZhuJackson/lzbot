import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OnebotAdapter

# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OnebotAdapter)

# 在这里加载插件
nonebot.load_builtin_plugins("echo")  # 内置插件
# nonebot.load_plugin("thirdparty_plugin")  # 第三方插件
nonebot.load_plugin("nonebot_plugin_status")
nonebot.load_plugin("nonebot_plugin_memes")
# nonebot.load_plugin("nonebot_plugin_dialectlist")
nonebot.load_plugin("nonebot_plugin_cloudsignx")
# nonebot.load_plugin("nonebot_plugin_learning_chat")
# nonebot.load_plugin("nonebot_plugin_setu_now")
nonebot.load_plugins("laozhubot/plugins")  # 加载所有本地插件

if __name__ == "__main__":
    nonebot.run()