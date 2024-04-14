# courscraper

A simple data scraper for coursera.

## Features

- Search course (TODO)
- Get course meta & syllabus
- Get course reviews
- Download videos & subtitles

## Usage

- Clone this repository
- Install requirements

```bash
pip install requirements.txt
```

- Copy "./courscraper" to your working directory

## Samples

### Get course infomation & reviews

```python
from courscraper import Scraper
from courscraper.misc import save_to_json

scraper = Scraper(dump_errors=True)

course = scraper.get_course_meta("https://www.coursera.org/learn/hanzi")
syllabus = scraper.get_course_syllabus(course.id)
reviews = scraper.get_course_reviews(course.id)

save_to_json(course.__dict__, f"{course.slug}.meta.json")
save_to_json(syllabus, f"{course.slug}.syllabus.json")
save_to_json(reviews, f"{course.slug}.reviews.json")
```

### Download video & subtitles

```python
import json
from courscraper import Scraper, Course_Json

# you can load data from files
with open("hanzi.meta.json", "r", encoding="utf8") as file:
    course = Course_Json(**json.load(file))
with open("hanzi.syllabus.json", "r", encoding="utf8") as file:
    syllabus = json.load(file)

scraper = Scraper(dump_errors=True)

for module in syllabus["modules"]:
    if "lecture" not in module["items"].keys():
        continue
    for lecture_data in module["items"]["lecture"]:
        lecture = scraper.get_lecture_meta(
            course,
            lecture_data["id"],
            resolution=540,  # 360 by default
            language_codes=["zh-CN"],  # ["zh-CN", "en"] by default
        )
        scraper.download_lecture(lecture, directory="./", sleep_time=1)
```
