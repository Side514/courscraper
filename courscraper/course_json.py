from dataclasses import dataclass


@dataclass
class Course_Json:
    url: str | None = None
    name: str | None = None
    id: str | None = None
    slug: str | None = None
    description: str | None = None
    learning_objectives: str | None = None
    photo_url: str | None = None
    primary_languages: list[str] | None = None
    subtitle_languages: list[str] | None = None
    enrollments: int | None = None
    partners: list[str] | None = None
    num_ratings: int | None = None
    avg_rating: float | None = None
