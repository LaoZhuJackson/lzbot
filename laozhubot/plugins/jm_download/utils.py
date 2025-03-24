import os
import time
from nonebot.log import logger
import asyncio
from nonebot import get_plugin_config
from PIL import Image

from laozhubot.plugins.jm_download.config import Config

plugin_config = get_plugin_config(Config)


class SpeedLimiter:
    def __init__(self):
        self.send_success_time = 0

    def send_success(self):
        self.send_success_time = time.time()

    async def async_speedlimit(self):
        if (delay_time := time.time() - self.send_success_time) < plugin_config.jm_send_interval:
            delay_time = round(delay_time, 2)
            logger.debug(f"Speed limit: Asyncio sleep {delay_time}s")
            await asyncio.sleep(delay_time)

