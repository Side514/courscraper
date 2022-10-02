# Python 3.7.9
# 爬取coursera特定课程的全部评论
from misc import save_to_json
from query_courses import get_course_ID
import time
import requests
import json
import re


def get_reviews(course_ID: str) -> list:
    """获取coursera特定课程的全部评论

    Args:
        course_ID (str): 课程ID

    Returns:
        list: 评论列表, 每条评论为dict格式
    """
    # 请求信息
    api = "https://www.coursera.org/graphqlBatch"  # 请求地址
    params = {"opname": "AllCourseReviews"}  # 请求参数
    payload = [
        {
            "operationName": "AllCourseReviews",
            "variables": {
                "courseId": course_ID,
                "limit": 65535,
                "start": "0",
                "ratingValues": [1, 2, 3, 4, 5],
                "productCompleted": None,
                "sortByHelpfulVotes": False,
            },
            "query": "query AllCourseReviews($courseId: String!, $limit: Int!, $start: String!, $ratingValues: [Int!], $productCompleted: Boolean, $sortByHelpfulVotes: Boolean!) {\nProductReviewsV1Resource {\nreviews: byProduct(productId: $courseId, ratingValues: $ratingValues, limit: $limit, start: $start, productCompleted: $productCompleted, sortByHelpfulVotes: $sortByHelpfulVotes) {\nelements {\n...ReviewFragment\n}\n}\n}\n}\n\nfragment ReviewFragment on ProductReviewsV1 {\nreviewedAt\nrating\nreviewText {\n... on ProductReviewsV1_cmlMember {\ncml {\nvalue\n}\n}\n}\nproductCompleted\n}\n",
        }
    ]  # 请求负载
    header = {
        "content-type": "application/json",
        "Host": "www.coursera.org",
        "Origin": "https://www.coursera.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53",
    }  # 请求头
    # 发送请求
    print("Requesting...")
    response = requests.post(api, params=params, json=payload, headers=header)
    response.encoding = response.apparent_encoding

    # 解析评论数据
    raw_data = json.loads(response.text)[0]["data"]["ProductReviewsV1Resource"]["reviews"]["elements"]
    reviews = []
    for item in raw_data:
        rating = item["rating"]  # 评分
        text = item["reviewText"]["cml"]["value"][12:-13]  # 评论文本
        text = text.replace("<text>", "").replace("</text>", "\n").replace("<text />", "\n").replace("\u200b", "")
        date = time.strftime("%Y-%m-%d", time.gmtime(item["reviewedAt"] / 1000))  # 评论时间
        completed = item["productCompleted"]  # 课程完成情况
        reviews.append({"rating": rating, "text": text, "date": date, "completed": completed})
    return reviews


def scrape(url: str):
    """爬取coursera特定课程的全部评论并保存

    Args:
        url (str): 课程首页网址
    """
    if re.search(r"coursera", url) is not None:
        if url.find("?") != -1:
            url = url[: url.find("?")]
        course_ID = get_course_ID(url)
        data = get_reviews(course_ID)
        course_name = url.split("/")[-1]
        if data:
            save_to_json(data, "coursera-" + course_name + ".json")
        else:
            print(f'No reviews found for "{course_name}".')
    else:
        print("Not supported site.")


if __name__ == "__main__":
    # 测试网址: https://www.coursera.org/learn/hanzi
    # 测试ID: COURSE~LZZg6vhQEeWfYgqbi1xsdw
    url = input("Enter a url: ")
    scrape(url)
