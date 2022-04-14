# -*- coding: utf-8 -*-
# Time       : 2022/4/15 3:42
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os
import random
import time
import webbrowser
from hashlib import sha256
from typing import Optional, List, Union
from urllib.parse import urlparse

import yaml
from cloudscraper import create_scraper
from lxml import etree
from selenium.common.exceptions import (
    InvalidCookieDomainException,
    WebDriverException,
    NoSuchCookieException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException

from .utils import ToolBox, get_ctx

logger = ToolBox.init_log()
# ---------------------------------------------------
# 工程目录定位
# ---------------------------------------------------
PROJECT_ROOT = os.path.dirname(__file__)
PROJECT_DATABASE = os.path.join(PROJECT_ROOT, "database")
DIR_COOKIES = os.path.join(PROJECT_DATABASE, "cookies")
PATH_CTX_COOKIES = os.path.join(DIR_COOKIES, "ctx_cookies.yaml")
# ---------------------------------------------------
# 路径补全
# ---------------------------------------------------
for _trace in [PROJECT_DATABASE, DIR_COOKIES]:
    if not os.path.exists(_trace):
        os.mkdir(_trace)


class _CookieManager:
    """管理上下文身份令牌"""

    URL_ACCOUNT_PERSONAL = "https://gitee.com/profile/account_information"

    def __init__(self, username: str, path_ctx_cookies: Optional[str] = None):
        self.username = username
        self.path_ctx_cookies = (
            "ctx_cookies.yaml" if path_ctx_cookies is None else path_ctx_cookies
        )

        self.action_name = "CookieManager"

    def _t(self) -> str:
        return (
            sha256(self.username[-3::-1].encode("utf-8")).hexdigest()
            if self.username
            else ""
        )

    def load_ctx_cookies(self) -> Optional[List[dict]]:
        if not os.path.exists(self.path_ctx_cookies):
            return []

        with open(self.path_ctx_cookies, "r", encoding="utf8") as file:
            data: dict = yaml.safe_load(file)

        ctx_cookies = data.get(self._t(), []) if isinstance(data, dict) else []
        if not ctx_cookies:
            return []

        logger.debug(
            ToolBox.runtime_report(
                motive="LOAD",
                action_name=self.action_name,
                message="Load context cookie.",
            )
        )

        return ctx_cookies

    def save_ctx_cookies(self, ctx_cookies: List[dict]) -> None:
        _data = {}

        if os.path.exists(self.path_ctx_cookies):
            with open(self.path_ctx_cookies, "r", encoding="utf8") as file:
                stream: dict = yaml.safe_load(file)
                _data = _data if not isinstance(stream, dict) else stream

        _data.update({self._t(): ctx_cookies})

        with open(self.path_ctx_cookies, "w", encoding="utf8") as file:
            yaml.dump(_data, file)

    def is_available_cookie(self, ctx_cookies: Union[List[dict], str] = None) -> bool:
        ctx_cookies = self.load_ctx_cookies() if ctx_cookies is None else ctx_cookies
        if not ctx_cookies:
            return False

        headers = {
            "cookie": ToolBox.transfer_cookies(ctx_cookies)
            if isinstance(ctx_cookies, list)
            else ctx_cookies
        }
        scraper = create_scraper()
        response = scraper.get(
            self.URL_ACCOUNT_PERSONAL, headers=headers, allow_redirects=False
        )
        return bool("第三方帐号绑定" in response.text)

    def reset_ctx_cookie(
        self, ctx_cookies: Optional[List[dict]] = None
    ) -> Optional[List[dict]]:
        ctx_cookies = self.load_ctx_cookies() if ctx_cookies is None else ctx_cookies
        if not self.is_available_cookie(ctx_cookies):
            logger.error(
                ToolBox.runtime_report(
                    action_name=self.action_name, motive="QUIT", message="Cookie 无效或已过期"
                )
            )
            return
        logger.success(
            ToolBox.runtime_report(
                motive="CHECK",
                action_name=self.action_name,
                message="The identity token is valid.",
            )
        )
        self.save_ctx_cookies(ctx_cookies)
        return ctx_cookies


class _AwesomeGitee:
    URL_TEMPLATE_REMOVE = "https://gitee.com{}/settings#remove"
    URL_ROOT = "https://gitee.com"

    def __init__(self, username: str, password: str, cookie: str, silence: bool = None):
        self.username = username.strip()
        self.password = password.strip()
        self.cookie = cookie
        self.silence = bool(silence)

        self.action_name = "FuckGitee"
        self.url_profile = f"https://gitee.com/{self.username}/projects"
        self.max_queue_size = 0
        self.banned_repos = {}

        self.logger = logger

    def __enter__(self):
        self._ctx_session = get_ctx(silence=self.silence)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if hasattr(self, "_ctx_session"):
                self._ctx_session.quit()
        except AttributeError:
            pass

    def _auth_reset(self, ctx):
        ctx.get(self.URL_ROOT)
        for cookie_dict in ToolBox.transfer_cookies(self.cookie):
            try:
                ctx.add_cookie(cookie_dict)
            except InvalidCookieDomainException:
                pass

    def _invalid_repo_filter(
        self, url, alert_message: str = "null", mode: str = "filter"
    ) -> Optional[bool]:
        if mode == "add":
            self.banned_repos.update({url: alert_message})
        elif mode == "filter":
            return bool(self.banned_repos.get(url))

    def _delete_repo(self, ctx: Chrome, url: str) -> Optional[bool]:
        ctx.get(url)
        namespace = urlparse(url).path.replace("/settings", "")[1:]

        # [√] 点击<删除仓库>
        try:
            WebDriverWait(ctx, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@data-tab='remove']//a[text()='删除仓库']")
                )
            ).click()
        except TimeoutException:
            try:
                alert_message = ctx.find_element(
                    By.XPATH, "//div[@class='block-title']"
                ).text
            except WebDriverException:
                pass
            else:
                self._invalid_repo_filter(
                    url, alert_message=alert_message.strip(), mode="add"
                )
                self.logger.warning(
                    ToolBox.runtime_report(
                        action_name="FuckGitee",
                        motive="REMOVE",
                        message=alert_message.strip(),
                        url=url,
                    )
                )
            finally:
                return

        # [√] 尝试修正命名空间
        try:
            time.sleep(0.3)
            namespace = ctx.find_element(
                By.XPATH, "//span[@class='highlight-black']"
            ).text
        except NoSuchCookieException:
            pass

        # [√] 输入确认删除的仓库路径
        WebDriverWait(ctx, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@id='path_with_namespace']")
            )
        ).send_keys(namespace)

        # [√] 点击<确认删除>
        time.sleep(0.2)
        ctx.find_element(By.XPATH, "//div[contains(text(),'确认删除')]").click()

        # [√] 输入用户密码
        WebDriverWait(ctx, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='_pavise_password']"))
        ).send_keys(self.password)

        # [√] 点击<验证> 删除仓库
        WebDriverWait(ctx, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@type='submit']"))
        ).click()

        return True

    def get_repo_details(self) -> Optional[List[str]]:
        """
        获取个人首页显示的至多20个仓库 href
        :return: ['/username/repoName1', '/username/repoName2']
        """
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.39",
            "cookie": self.cookie,
        }
        scraper = create_scraper()
        response = scraper.get(self.url_profile, headers=headers)
        tree = etree.HTML(response.content)
        hrefs = tree.xpath(
            "//ul[@id='search-projects-ulist']//a[@class='repository']/@href"
        )
        urls = []
        for href in hrefs:
            url = self.URL_TEMPLATE_REMOVE.format(href)
            if self._invalid_repo_filter(url, mode="filter"):
                continue
            urls.append(url)

        return urls

    def fuck_me_till_the_daylight(self):
        self._auth_reset(ctx=self._ctx_session)

        while True:
            urls = self.get_repo_details()
            if not urls:
                self.logger.success(
                    ToolBox.runtime_report(
                        action_name=self.action_name,
                        motive="DONE",
                        message="已删除所有可访问仓库",
                        bypass_repos=self.banned_repos,
                    )
                )
                return
            random.shuffle(urls)
            for url in urls:
                try:
                    response = self._delete_repo(self._ctx_session, url=url)
                    if response:
                        self.logger.debug(
                            ToolBox.runtime_report(
                                action_name=self.action_name,
                                motive="DELETE",
                                message="移除仓库",
                                url=url,
                            )
                        )
                except WebDriverException as err:
                    self.logger.warning(
                        ToolBox.runtime_report(
                            action_name=self.action_name,
                            motive="SKIP",
                            message=err.msg,
                            url=url,
                        )
                    )
                    continue


def _reset_cookie(
    username: str, ctx_cookies: Optional[List[dict]] = None
) -> Optional[List[dict]]:
    manager = _CookieManager(username, path_ctx_cookies=PATH_CTX_COOKIES)
    return manager.reset_ctx_cookie(ctx_cookies)


def _launcher(username: str, password: str, cookie: str):
    with _AwesomeGitee(username=username, password=password, cookie=cookie) as ag:
        ag.fuck_me_till_the_daylight()
    _show_hyperlink()


def _show_hyperlink():
    hyperlinks = {
        "项目被屏蔽后如何处理？": "https://gitee.com/help/articles/4201",
        "如何注销 Gitee 帐号？": "https://gitee.com/help/articles/4286#article-header1",
        "请使用「关联邮箱」发送邮件": "mailto:git@oschina.cn?subject=please-deregister-my-Gitee-account",
    }
    for message, url in hyperlinks.items():
        logger.info(
            ToolBox.runtime_report(
                action_name="Question", motive="ACCESS", message=message, url=url
            )
        )


@logger.catch()
def remove_all(username: str, password: str):
    """

    :param username: @username 输入`@`之后的内容，用于拼接仓库链接
    :param password: 用于仓库删除时需要验证密码
    :return:
    """
    if (
        not username
        or not password
        or not isinstance(username, str)
        or not isinstance(password, str)
    ):
        print(">>> <username> 或 <password> 参数不合法")
        return
    username = username.strip().replace("@", "")
    password = password.strip()
    profile_projects = f"https://gitee.com/{username}/projects"

    try:
        urlparse(profile_projects)
    except (TypeError, ValueError, UnicodeError):
        print(f">>> username 输入错误，无法拼接正常网址 - profile={profile_projects}")
        return

    try:
        ctx_cookies = _reset_cookie(username)
        if not ctx_cookies:
            usr_input = input(f">>> 请前往个人主页获取 Cookie, 输入[y]自动访问 --> {profile_projects}\n")
            if usr_input.lower() == "y":
                webbrowser.open(profile_projects)
            cookie = input(">>> Input your Cookie:\n- ")
            try:
                ctx_cookies = ToolBox.transfer_cookies(cookie)
                if not _reset_cookie(username, ctx_cookies):
                    return
            except IndexError:
                print(">>> Cookie 格式错误")
                return
    except (KeyboardInterrupt, EOFError):
        return
    else:
        cookie = (
            ctx_cookies
            if isinstance(ctx_cookies, str)
            else ToolBox.transfer_cookies(ctx_cookies)
        )
        _launcher(username, password, cookie)
