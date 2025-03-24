from pydantic import BaseModel, field_validator

class Config(BaseModel):
    downloader_reply_quote: bool = True
    downloader_reply_at:bool = False
    
    @field_validator('downloader_reply_quote','downloader_reply_at',mode='before')
    def check_reply_options(cls,v,info):
        if not isinstance(v,bool):
            raise ValueError(f"{info.field_name} must be a boolean")
        values = info.data
        if info.field_name=='downloader_reply_quote' and v and values.get('downloader_reply_at'):
            raise ValueError('引用回复和@回复不能同时为true')
        if info.field_name=='downloader_reply_at' and v and values.get('downloader_reply_quote'):
            raise ValueError('引用回复和@回复不能同时为true')