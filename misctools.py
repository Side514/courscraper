# Python 3.7.2
from typing import List
import json
import csv
import requests
from bs4 import BeautifulSoup


def get_soup(url: str, params: dict = None) -> BeautifulSoup:
    """请求指定的网页并解析为BeautifulSoup对象.

    Args:
        url (str): 网址.
        params (dict, optional): 参数. 默认为{}.

    Returns:
        BeautifulSoup: 解析后的html文档.
    """
    # 请求头
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44"
    }
    # 请求html
    response = requests.get(url, headers=header, params=params)
    response.encoding = response.apparent_encoding
    # 返回解析的html
    return BeautifulSoup(response.text, "lxml")


def save_to_json(data, filename: str):
    """将数据保存至json文件中.

    Args:
        data (Any): 数据.
        name (str): 文件名.
    """
    with open(filename, "w", encoding="utf-8") as output:
        # 不处理Unicode字符
        json.dump(data, output, indent=4, ensure_ascii=False)
    print(f"{len(data)} reviews have been saved to {filename}.")


def progress_bar(done: int, total: int):
    """显示/刷新计时进度条.

    Args:
        done (int): 当前完成任务数.
        total (int): 总任务数.
    """
    length = 50
    filled = "#" * int(length * done / total)
    empty = "." * int(length - len(filled))
    print(f"\rProgress: {done}/{total} [{filled}{empty}]", end="")
