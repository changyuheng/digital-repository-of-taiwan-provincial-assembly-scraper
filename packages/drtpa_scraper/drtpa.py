import logging
import os
import pathlib
import shutil
import stat
import time
from typing import Any, Callable, Optional, Union

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .config import Config
from .log import get_logger


class SimpleDrtpa:
    HOME_PAGE: str = "https://drtpa.th.gov.tw/index.php"
    LOGIN_PAGE: str = "https://drtpa.th.gov.tw/index.php?act=Landing/account#signin"
    ARCHIVE_INDEX_PAGE: str = "https://drtpa.th.gov.tw/index.php?act=Archive/index"

    def __init__(self, config: Config) -> None:
        self.cache_path: pathlib.Path = pathlib.Path("cache").absolute()
        self.config: Config = config

        self.clear_cache()

        LOGGER.setLevel(logging.WARNING)
        edge_options: webdriver.EdgeOptions = webdriver.EdgeOptions()
        edge_options.add_argument(f"user-data-dir={self.cache_path}")
        self.edge_driver: webdriver.Edge = webdriver.Edge(
            EdgeChromiumDriverManager().install(), options=edge_options)

    def clear_cache(self) -> None:
        def on_rm_error(func: Callable[[Any], None], path: str, exc_info: Any):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if self.cache_path.is_dir():
            shutil.rmtree(self.cache_path, onerror=on_rm_error)
        if not self.cache_path.is_dir():
            self.cache_path.mkdir()

    def login(self) -> None:
        e: Optional[TimeoutException] = None
        i: int
        for i in range(100):
            try:
                self.edge_driver.get(self.LOGIN_PAGE)
                d: webdriver.Edge
                WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.ID, 'uname'))
                WebDriverWait(self.edge_driver, 1).until(lambda d: d.find_element(By.ID, 'upass'))

                self.edge_driver.find_element(By.ID, 'uname').send_keys(self.config.account)
                self.edge_driver.find_element(By.ID, 'upass').send_keys(self.config.password)
                self.edge_driver.find_element(By.ID, 'act_signin').click()

                WebDriverWait(self.edge_driver, 15).until(lambda d: d.find_element(By.ID, 'signout'))
            except TimeoutException as e:
                get_logger().info(f"retry: {i+1}")
                time.sleep(1)
                continue
            else:
                break
        else:
            if e:
                raise e

    def _get_metas_from_search_result_links(self, links) -> list[dict[str: str]]:
        metas: list[dict[str: str]] = list()
        e: Optional[Union[ElementClickInterceptedException, TimeoutException]] = None
        search_window: str = self.edge_driver.current_window_handle

        link: WebElement
        for link in links:
            i: int
            for i in range(100):
                try:
                    link.click()
                    d: webdriver.Edge
                    WebDriverWait(self.edge_driver, 10).until(lambda d: len(d.window_handles) > 1)
                    self.edge_driver.switch_to.window(
                        self.edge_driver.window_handles[len(self.edge_driver.window_handles) - 1])
                    WebDriverWait(self.edge_driver, 10).until(
                        lambda d: d.find_element(By.CLASS_NAME, 'display_object_area'))
                except (ElementClickInterceptedException, TimeoutException) as e:
                    get_logger().info(f"retry: {i+1}")
                    while len(self.edge_driver.window_handles) > 1:
                        self.edge_driver.switch_to.window(
                            self.edge_driver.window_handles[len(self.edge_driver.window_handles) - 1])
                        self.edge_driver.close()
                    self.edge_driver.switch_to.window(search_window)
                    time.sleep(1)
                    continue
                else:
                    break
            else:
                if e:
                    raise e

            data_table: WebElement = self.edge_driver.find_element(By.CLASS_NAME, 'meta_table')
            field: WebElement
            value: WebElement
            meta: dict[str: str] = dict()
            for field, value in zip(
                    data_table.find_elements(By.CLASS_NAME, 'meta_field'),
                    data_table.find_elements(By.CLASS_NAME, 'meta_value')):
                if not field.text:
                    continue
                meta[field.text] = value.text
            metas.append(meta)

            self.edge_driver.close()
            self.edge_driver.switch_to.window(search_window)
        return metas

    def search(self, keyword: str) -> list[dict[str:str]]:
        results: list[dict[str: str]] = list()
        e: Optional[TimeoutException] = None

        i: int
        for i in range(100):
            try:
                self.edge_driver.get(self.ARCHIVE_INDEX_PAGE)
                d: webdriver.Edge
                WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.ID, 'search_input'))
                WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(By.ID, 'search_submit'))

                self.edge_driver.find_element(By.ID, 'search_input').clear()
                self.edge_driver.find_element(By.ID, 'search_input').send_keys(keyword)
                self.edge_driver.find_element(By.ID, 'search_submit').click()
                WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(
                    By.XPATH, f'//span[text()="{keyword}"]'))
            except TimeoutException as e:
                get_logger().info(f"retry: {i+1}")
                time.sleep(1)
                continue
            else:
                break
        else:
            if e:
                raise e

        if self.edge_driver.find_elements(By.CLASS_NAME, 'page_block'):
            for _ in range(500):
                # The commented method should be working but the website has a bug
                #   which causes the next button working improperly when the page is the second last one.
                # record_summary: WebElement = self.edge_driver.find_element(By.CLASS_NAME, "record_summary")
                # current_range: str = record_summary.find_element(
                #     By.XPATH, "//span[contains(text(),'顯示')]").text.replace("顯示", "").strip()
                # next_range: str = self.edge_driver.find_element(By.LINK_TEXT, "»").get_attribute('page').strip()
                # get_logger().info(f"record: {current_range}")
                # get_logger().info(f"record: {next_range}")
                #
                # results += self._get_metas_from_search_result_links(
                #     self.edge_driver.find_elements(By.PARTIAL_LINK_TEXT, "線上閱覽"))
                #
                # if current_range == next_range:
                #     break
                #
                # self.edge_driver.find_element(By.LINK_TEXT, "»").click()
                # WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(
                #     By.CLASS_NAME, "record_summary").find_element(
                #     By.XPATH, "//span[contains(text(),'顯示')]").text.replace("顯示", "").strip() != current_range)

                current_page: WebElement = self.edge_driver.find_element(
                    By.CLASS_NAME, "page_tap.page_now")
                next_page: WebElement = current_page
                if self.edge_driver.find_elements(
                        By.XPATH, "//a[@class='page_tap page_now']/following-sibling::a"):
                    next_page = self.edge_driver.find_element(
                        By.XPATH, '//a[@class="page_tap page_now"]/following-sibling::a')
                get_logger().info(f"current page: {current_page.text.strip()}")
                get_logger().info(f"next page: {next_page.text.strip()}")

                results += self._get_metas_from_search_result_links(
                    self.edge_driver.find_elements(By.PARTIAL_LINK_TEXT, "線上閱覽"))

                if current_page == next_page:
                    break

                current_page_text: str = current_page.text.strip()

                for i in range(100):
                    try:
                        next_page.click()
                        WebDriverWait(self.edge_driver, 10).until(lambda d: d.find_element(
                            By.CLASS_NAME, "page_tap.page_now").text.strip() != current_page_text)
                    except TimeoutException as e:
                        get_logger().info(f"retry: {i+1}")
                        time.sleep(1)
                        continue
                    else:
                        break
                else:
                    if e:
                        raise e
        return results