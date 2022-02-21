import json
from collections import defaultdict
from typing import Callable, Any


def parse(parsers: dict[str, Callable[[list[Any]], Any]]) -> dict[str, dict[str, Any]]:
    with open("crawler/interests.json", "r", encoding="utf-8") as interests_f:
        interests: dict = json.load(interests_f)

    ret = defaultdict(dict)
    for member, sections in interests.items():
        for section, entries in sections.items():
            if section in parsers:
                parsed = parsers[section](entries)
                ret[member][section] = parsed

    return ret
