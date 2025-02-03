import asyncio
import json
import os
import random
import sqlite3
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Union

from httpx import AsyncClient
from loguru import logger
from PIL import Image

from laozhubot.plugins.setu.config import config
from laozhubot.plugins.setu.fetch_resources import download_pic
from laozhubot.plugins.setu.permission_manager import pm


class GetData:
    def __init__(self) -> None:
        """
        初始化保存图片的路径以及该路径下的所有文件名
        """
        self.all_file_name: Dict[str, set] = {"nsfw": set(), "sfw": set()}
        if config.setu_save:
            self.all_file_name["nsfw"] = set(os.listdir(config.setu_nsfw_path))
            self.all_file_name["sfw"] = set(os.listdir(config.setu_sfw_path))
        self.database_path: Path = Path(__file__).parent / "resource/laozhu_setu.db"

    @staticmethod
    async def change_pixel(image, quality: int):
        """
        对图像进行处理，防止风控，图像镜像左右翻转, 并且随机修改左上角一个像素点
        :param image:
        :param quality:
        :return:
        """
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
        image = image.convert("RGB")
        image.load()[0, 0] = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        byte_data = BytesIO()
        image.save(byte_data, format="JPEG", quality=quality)
        return byte_data.getvalue()

    async def update_status_unavailable(self, urls: str) -> None:
        """
        更新数据库中的图片状态为unavailable

        params: urls: 图片的url
        """

        conn = sqlite3.connect(self.database_path)
        cur = conn.cursor()
        sql = f"UPDATE image_data set status='unavailable' where urls='{urls}'"  # 手搓sql语句
        cur.execute(sql)
        conn.commit()
        conn.close()

    async def get_setu(self, keywords: List[str], num: int = 1, r18: bool = False, quality: int = 75) -> List[list]:
        """
        :param keywords:关键词列表
        :param num:数量
        :param r18:是否r18
        :param quality:图片质量
        :return:返回列表,内容为setu消息(列表套娃)
        [
            [图片(bytes), data(图片信息), True(是否拿到了图), setu_url],
            [Error(错误), message(错误信息), False(是否拿到了图), setu_url]
        ]
        """
        data = []
        conn = sqlite3.connect(self.database_path)  # 连接数据库
        cur = conn.cursor()
        # sql操作,根据keyword和r18进行查询拿到数据
        if not keywords:
            # 未输入keywords时的查询语句
            # GROUP_CONCAT(t.tag_name, ', ') 用于将每张图片的多个标签合并成一个以逗号分隔的字符串。如果一张图片有多个标签，它们将被合并在一起，作为一个字符串返回
            # 由于 GROUP_CONCAT() 是聚合函数，GROUP BY m.pid 是必须的，这样可以确保每张图片（pid）对应一个结果行，同时将所有标签合并成一个字符串。
            sql = f"""
            SELECT m.pid,m.title,m.author,m.r18,GROUP_CONCAT(t.tag_name,'，') as tags,m.urls 
            from image_data m 
            LEFT JOIN image_tags it ON m.pid = it.pid 
            LEFT JOIN tags t ON it.tag_id = t.tag_id 
            WHERE m.r18 = {r18} AND m.status != 'unavailable' 
            GROUP BY m.pid 
            order by random() 
            limit {num}
"""
        elif len(keywords) == 1:
            sql = f"""
                SELECT m.pid, m.title, m.author, m.r18, GROUP_CONCAT(t.tag_name, ', ') AS tags, m.urls
                FROM image_data m
                LEFT JOIN image_tags it ON m.pid = it.pid
                LEFT JOIN tags t ON it.tag_id = t.tag_id
                WHERE (t.tag_name LIKE '%{keywords[0]}%' OR m.title LIKE '%{keywords[0]}%' OR m.author LIKE '%{keywords[0]}%')
                  AND m.r18 = {r18}
                  AND m.status != 'unavailable'
                GROUP BY m.pid
                ORDER BY RANDOM()
                LIMIT {num};
                """
        else:
            # 多tag的情况下的sql语句
            tag_sql = " AND ".join(
                f"t.tag_name LIKE '%{i}%'"
                for i in keywords
            )
            sql = f"""
                SELECT m.pid, m.title, m.author, m.r18, GROUP_CONCAT(t.tag_name, ', ') AS tags, m.urls
                FROM image_data m
                LEFT JOIN image_tags it ON m.pid = it.pid
                LEFT JOIN tags t ON it.tag_id = t.tag_id
                WHERE ({tag_sql}) 
                  AND m.r18 = {r18} 
                  AND m.status != 'unavailable'
                GROUP BY m.pid
                ORDER BY RANDOM()
                LIMIT {num};
                """
        # cur.execute(sql) 会执行查询，返回一个结果集。fetchall() 会把这个结果集提取出来，并以列表形式返回
        db_data = cur.execute(sql).fetchall()
        # 断开数据库连接
        conn.close()
        if not db_data:
            logger.warning(f"图库中没有搜到关于{keywords}的图, 即将随机产生一张")
            # 随机产生涩图
            data = await self.random_get_setu(keywords, num, r18, quality)
            if not data:
                raise ValueError(f"随机获取setu失败")
        else:
            # 如果找到了
            async with AsyncClient(proxy=config.scientific_agency) as client:
                tasks = [
                    self.pic(setu, quality, client, pm.read_proxy()) for setu in db_data
                ]
                data = await asyncio.gather(*tasks)
        return data

    async def pic(self, setu: List, quality: int, client: AsyncClient, setu_proxy: str):
        """
        :param setu:数据库中的一条数据
        :param quality:图片质量
        :param client:httpx的AsyncClient
        :param setu_proxy:反向代理的url
        :return:setu消息列表
        [Error(错误), message(错误信息), False(是否拿到了图), setu_url]
        或者
        [图片(bytes), data(图片信息), True(是否拿到了图), setu_url]
        """
        setu_pid: int = setu[0]  # pid
        setu_title: str = setu[1]  # 标题
        setu_author: str = setu[2]  # 作者
        setu_r18: str = "True" if setu[3] == 1 else "False"  # r18
        setu_tags: str = setu[4]  # 标签
        setu_url: str = setu[5].replace("i.pixiv.re", setu_proxy)  # 图片url

        data = f"标题:{setu_title}\npid:{setu_pid}\n画师:{setu_author}"
        logger.info(f"\n{data}\ntags:{setu_tags}\nR18:{setu_r18}")  # 打印信息
        file_name = setu_url.split("/")[-1]  # 获取文件名

        # 判断文件是否本地存在
        is_nsfw = setu_r18 == "True"
        # 当不保存的时候, save_path为False, 保存的时候,save_path为路径
        save_path: Union[bool, str] = (
            config.setu_nsfw_path if is_nsfw else config.setu_sfw_path
        )
        is_in_all_file_name = (
                file_name in self.all_file_name["nsfw" if is_nsfw else "sfw"]
        )
        if is_in_all_file_name:
            logger.info("本地存在该图片")
            try:
                image = Image.open(f"{save_path}/{file_name}")  # 尝试打开本地图片
            except Exception as e:
                return [
                    "Error",
                    f"本地图片打开失败, 错误信息: {repr(e)}\nfile_name:{file_name}",
                    False,
                    setu_url,
                ]
        else:
            logger.info(f"图片本地不存在,正在去{setu_proxy}下载")
            content: Union[bytes, int] = await download_pic(setu_url, client)
            # 如果返回的是int, 那么就是状态码, 表示下载失败
            if isinstance(content, int):
                # 如果是404, 404表示文件不存在, 说明作者删除了图片, 那么就把这个url的status改为unavailable, 下次sql操作的时候就不会再拿到这个url了
                if content == 404:
                    # setu[5]是原始url, 不能拿换过代理的url
                    await self.update_status_unavailable(setu[5])
                logger.error(f"图片下载失败, 状态码: {content}")  # 返回错误信息
                return ["Error", f"图片下载失败, 状态码: {content}", False, setu_url]
            # 错误处理, 如果content是空bytes, 那么Image.open会报错, 跳到except, 如果能打开图片, 图片应该不成问题,
            try:
                image = Image.open(BytesIO(content))  # 打开图片
            except Exception as e:
                return ["Error", f"图片打开失败, 错误信息: {repr(e)}", False, setu_url]
            # 保存图片, 如果save_path不为空, 以及图片不在all_file_name中, 那么就保存图片
            if save_path:
                try:
                    with open(f"{save_path}/{file_name}", "wb") as f:
                        f.write(content)
                    self.all_file_name["nsfw" if is_nsfw else "sfw"].add(file_name)
                except Exception as e:
                    logger.error(f"图片存储失败: {repr(e)}")
        try:
            # 尝试修改图片
            pic = await self.change_pixel(image, quality)
            return [pic, data, True, setu_url]
        except Exception as e:
            return ["Error", f"图片处理失败: {repr(e)}", False, setu_url]

    async def random_get_setu(self, keywords: List[str], num: int = 1, r18: bool = False, quality: int = 75):
        data = []
        async with AsyncClient() as client:
            try:
                tasks = [self.pic_random(keywords, r18, quality, client, pm.read_proxy()) for i in range(num)]
                data = await asyncio.gather(*tasks)
            except Exception as e:
                logger.error(f"api获取随机图片失败: {repr(e)}")
                return []
        return data

    async def pic_random(self, keywords: List[str], r18: bool, quality: int, client: AsyncClient, setu_proxy: str):
        tag = ''
        if keywords:
            for keyword in keywords:
                tag = tag + f"&tag={keyword}"
        r18 = 1 if r18 else 0
        api_url = f"https://api.lolicon.app/setu/v2?r18={r18}{tag}&excludeAI=1"
        res = await client.get(
            api_url
        )
        if res.status_code != 200:
            return ["Error", f"api获取图片失败，status_code: {res.status_code}", False, api_url]
        data = res.json()["data"][0]
        pid = data["pid"]
        p = data["p"]
        uid = data["uid"]
        title = data["title"]
        author = data["author"]
        r18 = data["r18"]
        width = data["width"]
        height = data["height"]
        ext = data["ext"]
        ai_type = data["aiType"]
        upload_date = data["uploadDate"]
        tags = data["tags"]
        urls = data["urls"]
        setu_url_origin = urls["original"]

        # 写入数据库
        conn = sqlite3.connect(self.database_path)  # 连接数据库
        cur = conn.cursor()
        # image_data表
        cur.execute('''
            INSERT OR IGNORE INTO image_data (pid, p, uid, title, author, r18, width, height, ext, ai_type, upload_date, urls, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pid, p, uid, title, author, r18, width, height, ext, ai_type, upload_date, setu_url_origin, 'available'
        ))
        # tags表
        for tag in tags:
            cur.execute('''
                                    INSERT OR IGNORE INTO tags (tag_name) VALUES (?)
                                ''', (tag,))
        # image_tags表
        for tag in tags:
            cur.execute('''
                                    SELECT tag_id FROM tags WHERE tag_name = ?
                                ''', (tag,))
            tag_id = cur.fetchone()
            if tag_id:
                tag_id = tag_id[0]
                cur.execute('''
                                        INSERT INTO image_tags (pid, tag_id) VALUES (?, ?)
                                    ''', (pid, tag_id))
        conn.commit()
        conn.close()
        # 尝试获取图片
        logger.debug(f"{r18=}")
        logger.debug(f"{type(r18)}")
        is_nsfw = r18
        save_path: Union[bool, str] = (
            config.setu_nsfw_path if is_nsfw else config.setu_sfw_path
        )

        setu_url: str = setu_url_origin.replace("i.pixiv.re", setu_proxy)  # 图片url
        file_name = setu_url.split("/")[-1]  # 获取文件名
        photo_info = f"标题:{title}\npid:{pid}\n画师:{author}"

        content: Union[bytes, int] = await download_pic(setu_url, client)
        # 如果返回的是int, 那么就是状态码, 表示下载失败
        if isinstance(content, int):
            logger.error(f"图片下载失败, 状态码: {content}")  # 返回错误信息
            return ["Error", f"图片下载失败, 状态码: {content}", False, setu_url]
        # 错误处理, 如果content是空bytes, 那么Image.open会报错, 跳到except, 如果能打开图片, 图片应该不成问题,
        try:
            image = Image.open(BytesIO(content))  # 打开图片
        except Exception as e:
            return ["Error", f"图片打开失败, 错误信息: {repr(e)}", False, setu_url]
        # 保存图片, 如果save_path不为空, 以及图片不在all_file_name中, 那么就保存图片
        if save_path:
            try:
                with open(f"{save_path}/{file_name}", "wb") as f:
                    f.write(content)
                self.all_file_name["nsfw" if is_nsfw else "sfw"].add(file_name)
            except Exception as e:
                logger.error(f"图片存储失败: {repr(e)}")
        try:
            # 尝试修改图片
            pic = await self.change_pixel(image, quality)
            return [pic, photo_info, True, setu_url]
        except Exception as e:
            return ["Error", f"图片处理失败: {repr(e)}", False, setu_url]


get_data = GetData()
