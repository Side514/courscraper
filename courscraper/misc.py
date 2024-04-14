import csv
import json


def is_supported_site(hostname: str) -> bool:
    supported_hostname = ["coursera.org", "www.coursera.org"]
    if hostname in supported_hostname:
        return True
    else:
        return False


def save_to_json(data, filepath: str):
    """Save data to a json file.

    Args:
        data (Any): any object which can be serialized by `json.dump()`
        filepath (str): save directory of json file
    """
    with open(filepath, "w", encoding="utf-8") as output:
        # keep Unicode characters
        json.dump(data, output, indent=2, ensure_ascii=False)
    print(f"{len(data)} items have been saved to {filepath}.")


def save_to_csv(data: list[dict[str, str]], filepath: str, fieldnames: list[str]):
    """Save data to a csv file, using UTF-8 by default.

    Args:
        data (list[dict]): each dict is as a row
        filepath (str): save directory of csv file
        fieldnames (list[str]): correspond to data
    """
    with open(filepath, "w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"{len(data)} items have been saved to {filepath}.")


def progress_bar(
    done: int, total: int, description: str = "Progress", wrap: bool = False
):
    """Display or refresh current task progress.

    Args:
        done (int): completed tasks
        total (int): total tasks
        description (str, optional): the string before the bar
        wrap (bool, optional): whether start a new line after printing the bar
    """
    if total <= 0 or done > total:
        return
    length = 50
    filled = "#" * int(length * done / total)
    empty = "." * int(length - len(filled))
    print(f"\r{description:<20}: {done}/{total} [{filled}{empty}]", end="")
    if wrap:
        print()
