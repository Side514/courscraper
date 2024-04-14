from urllib.parse import urlparse
from os.path import splitext


class Asset_Json:
    def __init__(self, url: str | None = None, id: str | None = None) -> None:
        self.url = url
        self.id = id

    def postfix(self) -> str:
        return ""

    def filename(self) -> str:
        prefix = self.id or "unknown_asset"
        return f"{prefix}.{self.postfix()}"


class Subtitles_Json(Asset_Json):
    def __init__(self, url: str, id: str, language_code: str) -> None:
        super().__init__(url, id)
        self.language_code = language_code

    def postfix(self) -> str:
        if self.language_code is None:
            return ""
        return f"{self.language_code}.vtt"


class Lecture_Json(Asset_Json):
    def __init__(
        self,
        url: str | None = None,
        id: str | None = None,
        resolution: str | None = None,
        subtitles: list[Subtitles_Json] = [],
    ) -> None:
        super().__init__(url, id)
        self.resolution = resolution
        self.subtitles = subtitles

    def postfix(self) -> str:
        if self.resolution is None:
            return ""
        path = urlparse(self.url).path
        extension = splitext(path)[-1]
        return f"{self.resolution}{extension}"
