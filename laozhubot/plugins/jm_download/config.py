from pydantic import BaseModel, field_validator
from nonebot import get_plugin_config
from typing import Set


class Config(BaseModel):
    superusers: Set[str]
    jm_downloader_reply_quote: bool = True
    jm_downloader_reply_at: bool = False
    # 全局发送间隔
    jm_send_interval: int = 3
    # 个人cd
    jm_personal_cd = 30
    jm_enable = True

    @field_validator('downloader_reply_quote', 'downloader_reply_at', mode='before')
    def check_reply_options(self, v, info):
        if not isinstance(v, bool):
            raise ValueError(f"{info.field_name} 必须得是布尔类型")
        values = info.data
        if info.field_name == 'downloader_reply_quote' and v and values.get('downloader_reply_at'):
            raise ValueError('引用回复和@回复不能同时为true')
        if info.field_name == 'downloader_reply_at' and v and values.get('downloader_reply_quote'):
            raise ValueError('引用回复和@回复不能同时为true')

