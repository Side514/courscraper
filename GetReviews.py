# Python 3.7.9
import requests
from bs4 import BeautifulSoup
import re
import time
import json


def progress_bar(done: int, total: int):
    """显示/刷新计时进度条

    Args:
        done (int): 当前完成任务数
        total (int): 总任务数
    """
    length = 50
    filled = "#" * int(length * done / total)
    empty = "." * int(length - len(filled))
    print(f"\rProgress: {done}/{total} [{filled}{empty}]", end="")


def save_to_json(data, name: str):
    """将数据保存至json文件中

    Args:
        data (Any): 数据
        name (str): 文件名
    """
    output = open(name, "w", encoding="utf-8")
    json.dump(data, output, indent=4, ensure_ascii=False)
    output.close()
    print(f"{len(data)} reviews have been saved to {name}.")


def get_soup(url: str) -> BeautifulSoup:
    """请求指定的网页并解析

    Args:
        url (str): 网址

    Returns:
        BeautifulSoup: 解析后的html文档
    """
    # 请求头
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.44"
    }
    # 请求html
    response = requests.get(url, headers=header)
    response.encoding = response.apparent_encoding
    # 返回解析的html
    return BeautifulSoup(response.text, "lxml")


def get_from_coursera(url: str) -> list:
    """获取coursera的某课程全部评论

    Args:
        url (str): 课程首页网址, 如https://www.coursera.org/learn/learn-chinese

    Returns:
        list: 课程信息
    """
    url += "/reviews?page="
    results = []
    page = 1
    # 获取第一页评论
    soup = get_soup(url + str(page))
    # 读取总页数
    total = int(soup.find("ul", class_="cui-buttonList").contents[-2].a.span.string)
    print(f"{total} pages in total.")
    while True:
        # 读取当前页面所有评论
        reviews = soup.find(class_="rc-ReviewsList").children
        reviews.__next__()
        for item in reviews:
            progress_bar(page, total)
            group = {}
            # 评星
            group["rating"] = int(len(item.find_all(id="FilledStardefault")))
            # 评论
            text = ""
            for p in item.find(class_="reviewText").div.div.children:
                if p.string is not None:
                    text += p.string
                text += "\n"
            group["text"] = text[:-1]
            # 认为有帮助
            helpful = re.search(
                r"\d+",
                item.find(class_="review-helpful-button").span.contents[-1].string,
            )
            if helpful is None:
                group["helpful"] = 0
            else:
                group["helpful"] = int(helpful.group())
            # 评论者名称
            group["name"] = item.find(class_="reviewerName").span.string[3:]
            # 日期
            group["date"] = item.find(class_="dateOfReview").string
            results.append(group)
        # 获取下一页
        page += 1
        if page > total:
            break
        soup = get_soup(url + str(page))
        # 等待时间
        time.sleep(2)
    print("\n", end="")
    return results


if __name__ == "__main__":
    print("Enter a url: ", end="")
    # 测试网址: https://www.coursera.org/learn/learn-chinese
    url = input()
    if re.search(r"coursera", url) is not None:
        if url.find("?") != -1:
            url = url[: url.find("?")]
        data = get_from_coursera(url)
        save_to_json(data, "coursera-" + url.split("/")[-1] + ".json")
    else:
        print("Not supported site.")
