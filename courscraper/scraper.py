from html2text import HTML2Text
from os.path import exists
from time import sleep
from urllib.parse import urlparse

from .apis import Apis
from .asset_json import Lecture_Json, Subtitles_Json
from .course_json import Course_Json
from .misc import is_supported_site


class Scraper:
    def __init__(
        self,
        dump_errors: bool = False,
        dump_dir: str | None = None,
        proxy: dict | None = None,
    ) -> None:
        """Initialize a scraper.

        Args:
            dump_errors (bool, optional): whether to dump error message when API errors. Defaults to False.
            dump_dir (str | None, optional): directory where error file saves.
            proxy (dict | None, optional): proxy for `requests` libarary.
        """
        self.__apis = Apis(proxy=proxy, dump_errors=dump_errors, dump_dir=dump_dir)

    def get_course_meta(self, course_url: str) -> Course_Json:
        """Get basic information of a course.

        Args:
            course_url (str): index URL of the course
        """
        parsed_url = urlparse(course_url)
        if not is_supported_site(parsed_url.hostname):
            raise RuntimeError(f"not supported site ({course_url})")
        course_url = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
        course = Course_Json(url=course_url)

        # query the course
        slug = parsed_url.path.split("/")[-1]
        raw_data = self.__apis.api_courses(slug)

        course.name = raw_data["name"]
        course.id = raw_data["id"]
        course.slug = raw_data["slug"]
        course.description = raw_data["description"]
        course.photo_url = (
            raw_data["photoUrl"]
            + "?auto=format%2Ccompress%2Cenhance&dpr=1&fit=fill&w=600"
        )
        course.primary_languages = raw_data["primaryLanguages"]
        course.subtitle_languages = raw_data["subtitleLanguages"]
        course.learning_objectives = ""
        if len(raw_data["learningObjectives"]) > 0:
            html_parser = HTML2Text()
            html_parser.body_width = 0
            for item in raw_data["learningObjectives"]:
                course.learning_objectives += html_parser.handle(
                    item["definition"]["value"]
                )

        # add more fields
        raw_data = self.__apis.api_search_course(
            course.name, "objectUrl", parsed_url.path
        )
        course.enrollments = raw_data["enrollments"]
        course.partners = raw_data["partners"]
        course.num_ratings = raw_data["numProductRatings"]
        course.avg_rating = raw_data["avgProductRating"]

        return course

    def get_course_syllabus(self, course_id: str) -> dict:
        """Get syllabus of the course.

        Args:
            course_id (str): course ID in coursera

        Returns:
            dict: metadata of course content
        """
        syllabus = {}
        item_counts = {}
        raw_data = self.__apis.api_course_materials(course_id)

        for module in raw_data["onDemandCourseMaterialModules.v1"]:
            learningObjectives = []
            if module["learningObjectives"]:
                learningObjectives = self.__apis.api_learning_objectives(
                    module["learningObjectives"]
                )

            module_id = module["id"]
            syllabus[module_id] = {
                "name": module["name"],
                "slug": module["slug"],
                "id": module_id,
                "description": module["description"],
                "learningObjectives": learningObjectives,
                "timeCommitment": module["timeCommitment"] // 60000,
                "items": {},
            }

        for item in raw_data["onDemandCourseMaterialItems.v2"]:
            # item statistics for this course
            item_type = item["contentSummary"]["typeName"]
            if item_type not in item_counts.keys():
                item_counts[item_type] = 0
            item_counts[item_type] += 1

            # add items to module["items"] by type
            module_id = item["moduleId"]
            module = syllabus[module_id]
            if item_type not in module["items"].keys():
                module["items"][item_type] = []
            module["items"][item_type].append(
                {
                    "name": item["name"],
                    "id": item["id"],
                    "slug": item["slug"],
                    "isLocked": item["isLocked"],
                    "timeCommitment": item["timeCommitment"] // 60000,
                }
            )

        return {
            "course_id": course_id,
            "itemCounts": item_counts,
            "modules": list(syllabus.values()),
        }

    def get_course_reviews(self, course_id: str, after: int = 0) -> list[dict]:
        """Get all reviews of the course.

        Args:
            course_id (str): course ID in coursera
            after (int, optional): timestamp, reviews published before will be ignored. Defaults to 0.

        Returns:
            list[dict]: reviews list
        """
        reviews = []
        raw_data = self.__apis.api_reviews(course_id, after)

        for item in raw_data:
            html_parser = HTML2Text()
            html_parser.body_width = 0
            text = html_parser.handle(item["reviewText"]["cml"]["value"])
            reviews.append(
                {
                    "rating": item["rating"],
                    "text": text,
                    "helpfulCount": item["mostHelpfulVoteCount"] or 0,
                    "reviewedAt": item["reviewedAt"],
                    "isCompleted": item["productCompleted"],
                }
            )

        return reviews

    def get_lecture_meta(
        self,
        course: Course_Json,
        lecture_id: str,
        resolution: int = 360,
        language_codes: list[str] = ["zh-CN", "en"],
    ) -> Lecture_Json:
        """Get lecture information.

        Args:
            course (Course_Json): the related course
            lecture_id (str): coursera id of the lecture
            resolution (int, optional): resolution of lecture video, can be 240, 360, 540, 720. Defaults to 360(P).
            language_codes (list[str], optional): expected languages of subtitles. Defaults to ["zh-CN", "en"].

        Raises:
            RuntimeError: when course information is invalid
            RuntimeError: when multiple videos in one lecture
            RuntimeError: when no video found in the lecture

        Returns:
            Lecture_Json: lecture meta
        """
        if course.id is None or course.primary_languages is None:
            raise RuntimeError(
                "course information not provided (id, primary_languages)"
            )
        lecture = Lecture_Json(id=lecture_id, subtitles=[])

        raw_data = self.__apis.api_lecture_videos(course.id, lecture_id)
        if len(raw_data) > 1:
            raise RuntimeError("multiple videos in one lecture", raw_data)
        raw_data = raw_data[0]

        video_data = raw_data["sources"]["byResolution"]
        for r in [f"{resolution}p", "360p", "540p", "720p", "240p"]:
            if r in video_data.keys():
                lecture.resolution = r
                lecture.url = video_data[r]["mp4VideoUrl"]
                break
        if lecture.url is None:
            raise RuntimeError(
                f"no video found in the lecture ({lecture_id})", raw_data
            )

        subtitles_data = raw_data["subtitlesVtt"]
        language_codes = set(course.primary_languages + ["zh-CN", "en"])
        for code in language_codes:
            if code in subtitles_data.keys():
                lecture.subtitles.append(
                    Subtitles_Json(
                        "https://www.coursera.org" + subtitles_data[code],
                        lecture_id,
                        code,
                    )
                )
        if lecture.subtitles == []:
            print(f"no subtitles found in lecture ({lecture_id})")
            print(raw_data)

        return lecture

    def download_lecture(
        self,
        lecture: Lecture_Json,
        directory: str = "./",
        sleep_time: int = 0,
        include_subtitles: bool = True,
    ) -> None:
        if lecture.url is None:
            print("no URL provided")
            return
        path = f"{directory}/{lecture.filename()}"
        if exists(path):
            print(f"{path} exists")
            return
        self.__apis.download_asset(lecture.url, path)
        sleep(sleep_time)

        if not include_subtitles:
            return
        for subtitles in lecture.subtitles:
            path = f"{directory}/{subtitles.filename()}"
            if exists(path):
                print(f"{path} exists")
                return
            self.__apis.download_asset(subtitles.url, path)
