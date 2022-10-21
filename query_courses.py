# Python 3.7.2
# 按特定关键词查找coursera课程列表
from misc import save_to_csv, progress_bar
import time
import requests
import json


def query_courses(query: str) -> list:
    """获取coursera按特定关键词查找的课程列表

    Args:
        query (str): 查询关键字

    Returns:
        list: 课程信息列表, 每门课程信息为dict格式
    """

    def query_more(page: int = 0) -> dict:
        """按page号请求课程数据.

        Args:
            page (int, optional): page号. Defaults to 0.

        Returns:
            dict: 课程信息.
        """
        # 请求信息
        url = "https://lua9b20g37-dsn.algolia.net/1/indexes/*/queries"
        # payload可添加参数获得搜索结果的统计数据
        # 默认统计项目
        # &facets=%5B%22topic%22%2C%22skills%22%2C%22productDifficultyLevel%22%2C%22productDurationEnum%22%2C%22entityTypeDescription%22%2C%22partners%22%2C%22allLanguages%22%5D
        # 每项目的最大条目数
        # &maxValuesPerFacet=1000
        payload = {
            "requests": [
                {
                    "indexName": "prod_all_launched_products_term_optimization",
                    "params": "query=" + query + "&hitsPerPage=100&page=" + str(page) + "&ruleContexts=%5B%22zh%22%5D",
                }
            ]
        }
        params = {
            "x-algolia-application-id": "LUA9B20G37",
            "x-algolia-api-key": "dcc55281ffd7ba6f24c3a9b18288499b",
        }
        header = {
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53",
        }
        # 发送请求
        response = requests.post(url, json=payload, params=params, headers=header)
        response.encoding = response.apparent_encoding
        # 解析并返回数据
        return json.loads(response.text)["results"][0]

    print("Querying...")
    results = []
    page = 0
    data = query_more()
    # 返回课程数量和总page数
    counts = data["nbHits"]
    if counts == 0:
        return results
    total = data["nbPages"]

    while True:
        # 获取当前页面的课程数据
        for item in data["hits"]:
            progress_bar(page + 1, total)
            group = {}
            group["链接"] = "https://www.coursera.org" + item["objectUrl"]
            group["课程名"] = item["name"]
            group["提供方"] = item["partners"][0]
            group["注册人数"] = item["enrollments"]
            group["评价人数"] = item["numProductRatings"]
            group["评分"] = item["avgProductRating"]
            group["难度级别"] = item["productDifficultyLevel"]
            group["学习计划"] = item["entityType"]
            group["课程长度"] = item["productDurationEnum"]
            group["平均学习时长"] = item["avgLearningHours"]
            group["技能标签"] = item["skills"]
            group["授课语言"] = item["language"]
            group["字幕语言"] = item["subtitleLanguage"]
            results.append(group)
        # 获取下一页
        page += 1
        if page >= total:
            break
        time.sleep(2)
        data = query_more(page)
    print("\n", end="")
    return results


def get_course_ID(url: str) -> str:
    """通过url获取课程ID

    Args:
        url (str): 课程首页网址

    Returns:
        str: 课程ID
    """
    # 请求信息
    api = "https://lua9b20g37-dsn.algolia.net/1/indexes/*/queries"
    payload = {
        "requests": [
            {
                "indexName": "prod_all_launched_products_term_optimization",
                "params": "query=" + url.split("/")[-1] + "&hitsPerPage=5&page=0",
            }
        ]
    }
    params = {
        "x-algolia-application-id": "LUA9B20G37",
        "x-algolia-api-key": "dcc55281ffd7ba6f24c3a9b18288499b",
    }
    header = {
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53",
    }
    # 发送请求
    response = requests.post(api, json=payload, params=params, headers=header)
    response.encoding = response.apparent_encoding
    hit_courses = json.loads(response.text)["results"][0]["hits"]
    for course in hit_courses:
        if "https://www.coursera.org" + course["objectUrl"] == url:
            return course["objectID"].replace("course", "COURSE")
    raise SystemExit("Get courseID failed!")


def scrape(query: str):
    """爬取coursera按特定关键词查找的课程列表并保存

    Args:
        query (str): 查询关键字
    """
    data = query_courses(query)
    if data:
        save_to_csv(data, "list-" + query + ".csv", data[0].keys())


if __name__ == "__main__":
    query = input("Enter a query: ")
    scrape(query)
