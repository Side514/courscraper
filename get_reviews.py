# Python 3.7.9
# 爬取coursera特定课程的全部评论
from misctools import save_to_json
from misctools import progress_bar
from misctools import get_soup
import re
import time


def get_from_coursera(url: str) -> list:
    """获取coursera特定课程的全部评论

    Args:
        url (str): 课程首页网址

    Returns:
        list: 评论列表, 每条评论为dict格式
    """
    print("Requesting...")
    results = []
    # 获取第一页评论, 按时间顺序
    url += "/reviews"
    params = {"page": 1, "sort": "recent"}
    soup = get_soup(url, params=params)

    # 获取评论总页数
    total = soup.find("ul", class_="cui-buttonList")
    if total is None:
        return results
    total = int(total.contents[-2].a.span.string)
    print(f"{total} pages in total.")

    while True:
        # 获取当前页面所有评论
        reviews = soup.find(class_="rc-ReviewsList").children
        reviews.__next__()
        for item in reviews:
            progress_bar(params["page"], total)
            group = {}
            # 评星
            group["rating"] = int(len(item.find_all(id="FilledStardefault")))
            # 评论
            text = ""
            for p in item.find(class_="reviewText").div.div.children:
                if p.string is not None:
                    text += p.string
                text += " \n "
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
        params["page"] += 1
        if params["page"] > total:
            break
        time.sleep(2)
        soup = get_soup(url, params=params)
    print("\n", end="")
    return results


def scrape(url: str):
    """爬取coursera特定课程的全部评论并保存

    Args:
        url (str): 课程首页网址
    """
    if re.search(r"coursera", url) is not None:
        if url.find("?") != -1:
            url = url[: url.find("?")]
        data = get_from_coursera(url)
        course_name = url.split("/")[-1]
        if data:
            save_to_json(data, "coursera-" + course_name + ".json")
        else:
            print(f'No reviews found for "{course_name}".')
    else:
        print("Not supported site.")


if __name__ == "__main__":
    # 测试网址: https://www.coursera.org/learn/hanzi
    url = input("Enter a url: ")
    scrape(url)
