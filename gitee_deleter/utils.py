# -*- coding: utf-8 -*-
# Time       : 2022/4/15 4:03
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os
import sys
from typing import Optional, List
from typing import Union, Dict

from loguru import logger
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_ctx(silence: Optional[bool] = None):
    """普通的 Selenium 驱动上下文，用于常规并发任务"""
    options = ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_argument("--disable-dev-shm-usage")
    if "linux" in sys.platform:
        silence = True
        options.add_argument("--no-sandbox")
    if silence is True:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")

    # 统一挑战语言
    os.environ["LANGUAGE"] = "zh"
    options.add_argument(f"--lang={os.getenv('LANGUAGE', '')}")

    # 使用 ChromeDriverManager 托管服务，自动适配浏览器驱动
    service = Service(ChromeDriverManager(log_level=0).install())
    return Chrome(options=options, service=service)  # noqa


class ToolBox:
    @staticmethod
    def init_log():
        """初始化 loguru 日志信息"""
        event_logger_format = (
            "<g>{time:YYYY-MM-DD HH:mm:ss}</g> | "
            "<lvl>{level}</lvl> - "
            # "<c><u>{name}</u></c> | "
            "{message}"
        )
        logger.remove()
        logger.add(
            sink=sys.stdout,
            colorize=True,
            level="DEBUG",
            format=event_logger_format,
            diagnose=False,
        )
        return logger

    @staticmethod
    def runtime_report(
        action_name: str, motive: str = "RUN", message: str = "", **params
    ) -> str:
        """格式化输出"""
        flag_ = f">> {motive} [{action_name}]"
        if message != "":
            flag_ += f" {message}"
        if params:
            flag_ += " - "
            flag_ += " ".join([f"{i[0]}={i[1]}" for i in params.items()])

        return flag_

    @staticmethod
    def transfer_cookies(
        api_cookies: Union[List[Dict[str, str]], str]
    ) -> Union[str, List[Dict[str, str]]]:
        """
        将 cookies 转换为可携带的 Request Header
        :param api_cookies: api.get_cookies() or cookie_body
        :return:
        """
        if isinstance(api_cookies, str):
            return [
                {"name": i.split("=")[0], "value": i.split("=")[1]}
                for i in api_cookies.split("; ")
            ]
        return (
            "; ".join([f"{i['name']}={i['value']}" for i in api_cookies])
            .encode("utf-8")
            .decode("latin1")
        )
