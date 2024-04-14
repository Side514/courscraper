import requests
import json
import time
from functools import wraps

from .misc import progress_bar


HEADERS = {
    "accept": "application/json",
    "accept-encoding": "gzip",
    "accept-language": "en",
    "origin": "https://www.coursera.org",
    "referer": "https://www.coursera.org/learn/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


class ApiError(Exception):
    def __init__(self, description: str, status_code: int, json=None) -> None:
        self.description = description
        self.status_code = status_code
        self.json = json or ""

    def __str__(self):
        return repr(
            f"\nAPI errors [{self.status_code}]: {self.description}\n{self.json}"
        )

    def asdict(self):
        return {
            "description": self.description,
            "code": self.status_code,
            "json": self.json,
        }


class Apis:
    def __init__(
        self,
        dump_errors: bool = False,
        dump_dir: str | None = None,
        proxy: dict | None = None,
    ) -> None:
        self.dump_errors = dump_errors
        if dump_errors:
            self.dump_dir = dump_dir or "./"
        self.proxy = proxy or {}

    @staticmethod
    def logger(api_func):
        @wraps(api_func)
        def decorated(self, *args, **kwargs):
            print(f"\rAPI requesting ({api_func.__name__})... ", end="", flush=True)
            try:
                result = api_func(self, *args, **kwargs)
            except ApiError as error:
                print(error)
                if self.dump_errors:
                    current_time = time.strftime("%m-%d %H:%M:%S", time.localtime())
                    with open(
                        f"{self.dump_dir}/api_error[{current_time}].json",
                        "w",
                        encoding="utf8",
                    ) as file:
                        json.dump(error.asdict(), file)
            print("Done", flush=True)
            return result

        return decorated

    @logger
    def api_courses(self, slug: str) -> dict:
        """API for basic course information.

        Args:
            slug (str): URL name of the course

        Raises:
            ApiError: when the course slug inexists

        Returns:
            dict: course information
        """
        api = "https://www.coursera.org/api/courses.v1"
        params = {
            "q": "slug",
            "slug": slug,
            "fields": "description,primaryLanguages,subtitleLanguages,photoUrl,learningObjectives",
        }
        response = requests.get(api, params=params, headers=HEADERS, proxies=self.proxy)
        if response.status_code >= 400:
            raise ApiError(
                f"cannot find the course by slug {slug}",
                response.status_code,
                response.json(),
            )
        return response.json()["elements"][0]

    @logger
    def api_course_materials(self, course_id: str) -> dict:
        """API for course syllabus.

        Args:
            course_id (str): course ID in coursera

        Raises:
            ApiError: when course ID inexists

        Returns:
            dict: syllabus information
        """
        api = f"https://www.coursera.org/api/onDemandCourseMaterials.v2/{course_id}"
        params = {
            "includes": "modules,items",
            # field for lessons:
            # onDemandCourseMaterialLessons.v1(name,slug,timeCommitment,elementIds,optional)
            "fields": "onDemandCourseMaterialModules.v1\
                (name,slug,description,timeCommitment,optional,learningObjectives),\
                    onDemandCourseMaterialItems.v2\
                (name,originalName,slug,timeCommitment,contentSummary,isLocked,lockableByItem,\
                lockedStatus,itemLockSummary)",
            "showLockedItems": "true",
        }
        response = requests.get(api, params=params, headers=HEADERS, proxies=self.proxy)
        if response.status_code >= 400:
            raise ApiError(
                f"cannot query syllabus of course({course_id})",
                response.status_code,
                response.json(),
            )
        return response.json()["linked"]

    @logger
    def api_lecture_videos(self, course_id: str, item_id: str) -> list[dict]:
        """API for lecture videos information.

        Args:
            course_id (str): course ID in coursera
            item_id (str): item ID in coursera

        Raises:
            ApiError: when video inexists

        Returns:
            list[dict]: video information
        """
        api = f"https://www.coursera.org/api/onDemandLectureVideos.v1/{course_id}~{item_id}"
        params = {
            "includes": "video",
            "fields": "onDemandVideos.v1(sources,subtitles,subtitlesVtt,subtitlesTxt,subtitlesAssetTags)",
        }
        response = requests.get(api, params=params, headers=HEADERS, proxies=self.proxy)
        if response.status_code >= 400:
            raise ApiError(
                f"no item found {course_id}~{item_id}",
                response.status_code,
                response.json(),
            )
        return response.json()["linked"]["onDemandVideos.v1"]

    @logger
    def api_learning_objectives(self, objective_ids: list[str]) -> list[str]:
        """API for learning objective information.

        Args:
            objective_id (list[str]): learning objective ID in coursera

        Raises:
            ApiError: when learning objective inexists

        Returns:
            list[str]: learning objective strings
        """
        api = "https://www.coursera.org/api/onDemandLearningObjectives.v2/"
        params = {
            "ids": ",".join(objective_ids),
            "fields": "id,description",
        }
        response = requests.get(api, params=params, headers=HEADERS, proxies=self.proxy)
        if response.status_code >= 400:
            raise ApiError(
                "no learning objective found",
                response.status_code,
                response.json(),
            )
        objectives = []
        for item in response.json()["elements"]:
            objectives.append(item["description"])
        return objectives

    @logger
    def api_search_course(
        self,
        query: str,
        validation_field: str | None = None,
        validation_content: str | None = None,
    ) -> list:
        """API for course searching. It will return course information as well.

        Args:
            query (str): query string
            validation_field (str | None): field name for finding specific course
            validation_content (str | None): field content for finding specific course

        Raises:
            ApiError: when cannot find the course or validation failed

        Returns:
            dict: course information
        """
        api = "https://lua9b20g37-3.algolianet.com/1/indexes/*/queries"
        params = {
            "x-algolia-application-id": "LUA9B20G37",
            "x-algolia-api-key": "dcc55281ffd7ba6f24c3a9b18288499b",
        }
        # more query params of payload["requests"][0]["params"] for result statistics:
        # &facets=%5B%22topic%22%2C%22skills%22%2C%22productDifficultyLevel%22%2C%22productDurationEnum%22%2C%22entityTypeDescription%22%2C%22partners%22%2C%22allLanguages%22%5D
        # &maxValuesPerFacet=1000
        payload = {
            "requests": [
                {
                    "indexName": "prod_all_launched_products_term_optimization",
                    # query 10 items to guarantee finding the target course
                    "params": f"query={query}&hitsPerPage=10&page=0",
                }
            ]
        }
        response = requests.post(
            api, json=payload, params=params, headers=HEADERS, proxies=self.proxy
        )
        for item in response.json()["results"][0]["hits"]:
            if item[validation_field] == validation_content:
                return item
        raise ApiError(
            f"cannot find the course by query {query}",
            response.status_code,
            response.json(),
        )

    @logger
    def api_reviews(self, course_id: str, after: int = 0) -> list[dict]:
        """API for course reviews. Multiple requests will be sent when needed.

        Args:
            course_id (str): course ID in coursera
            after (int, optional): timestamp, reviews published before will be ignored. Defaults to 0

        Raises:
            ApiError: when course ID inexists

        Returns:
            list[dict]: course reviews
        """

        def request(start: int, proxy: dict):
            api = "https://www.coursera.org/graphql-gateway-wrapper"
            params = {"opname": "AllCourseReviews"}
            graphql = "query AllCourseReviews($courseId: String!, $limit: Int!, $start: String!, $ratingValues: [Int!],\
                $productCompleted: Boolean, $sortByHelpfulVotes: Boolean!) {\nProductReviewsV1Resource {\n\
                reviews: byProduct(\nproductId: $courseId\nratingValues: $ratingValues\nlimit: $limit\nstart: $start\n\
                productCompleted: $productCompleted\nsortByHelpfulVotes: $sortByHelpfulVotes\n) {\nelements {\n\
                ...ReviewFragment\n}\npaging {\ntotal\n}\n}\n}\n}\nfragment ReviewFragment on ProductReviewsV1 {\n\
                reviewedAt\nrating\nreviewText {\n... on ProductReviewsV1_cmlMember {\ncml {\nvalue\n}\n}\n}\n\
                productCompleted\nmostHelpfulVoteCount\n}"
            payload = [
                {
                    "operationName": "AllCourseReviews",
                    "variables": {
                        "courseId": "COURSE~" + course_id,
                        "limit": 1000,
                        "start": str(start),
                        "ratingValues": [1, 2, 3, 4, 5],
                        "productCompleted": None,
                        "sortByHelpfulVotes": False,
                    },
                    "query": graphql,
                }
            ]
            print(f"\r\tRequesting ({start}~)...", end="", flush=True)
            response = requests.post(
                api, params=params, json=payload, headers=HEADERS, proxies=proxy
            )
            if response.status_code >= 400:
                raise ApiError(
                    f"cannot fetch reviews of course({course_id})",
                    response.status_code,
                    response.json(),
                )
            return response.json()[0]["data"]["ProductReviewsV1Resource"]["reviews"]

        def add_to_result_and_is_over(result: list, fetched_reviews: list) -> bool:
            if fetched_reviews[-1]["reviewedAt"] > after:
                result.extend(fetched_reviews)
                return False  # not over, need fetch more
            # descending list, bisearch
            lower_bound = 0
            upper_bound = len(fetched_reviews)
            while lower_bound < upper_bound:
                target = lower_bound + (upper_bound - lower_bound) // 2
                if fetched_reviews[target]["reviewedAt"] > after:
                    lower_bound = target + 1
                else:
                    upper_bound = target
            result.extend(fetched_reviews[:lower_bound])
            return True  # over, needn't fetch more

        print("")  # wrap
        start = 0
        reviews = []

        raw_data = request(start, self.proxy)
        start += 1000
        if add_to_result_and_is_over(reviews, raw_data["elements"]):
            return reviews

        total = raw_data["paging"]["total"]
        while total > start:
            raw_data = request(start, self.proxy)
            start += 1000
            if add_to_result_and_is_over(reviews, raw_data["elements"]):
                break

        return reviews

    @logger
    def download_asset(self, url: str, save_path: str):
        """Download assets, such as video.

        Args:
            url (str)
            save_path (str)

        Raises:
            ApiError: when download failed
        """
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        }
        response = requests.get(url, headers=headers, proxies=self.proxy, stream=True)
        if response.status_code >= 400:
            raise ApiError(
                "failed to download file",
                response.status_code,
                response.json(),
            )

        chunk_size = 1024 * 512
        total = int(response.headers.get("content-length") or -1)
        progress = 0
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    progress += chunk_size
                    progress_bar(progress, total, save_path)
