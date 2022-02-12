import re
from datetime import date
from typing import Tuple, Optional, List


def strip_registration_date(entry: str) -> Tuple[str, List[date]]:
    pattern = re.compile(r"\((?:Registered|Updated|First registered) (\d\d? [A-Z][a-z]+ \d\d\d\d)(?:.+(\d\d? [A-Z][a-z]+ \d\d\d\d))*?\)")
    matches = pattern.search(entry)
    stripped = pattern.sub("", entry)
    if matches is not None:
        return stripped, list(matches.groups())
    else:
        return stripped, []
