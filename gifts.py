import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Union, Tuple

import parser
from utils import strip_registration_date


@dataclass
class Gift:
    donor_name: str
    donor_address: str
    content: str
    value: Decimal
    date_received: Union[date, Tuple[date, date]]  # sometimes they give a date range
    date_accepted: date
    donor_type: str


def extract_value(amount_str: str) -> Decimal:
    def fixed_point(money_str: str) -> Decimal:
        money_str = money_str.removeprefix("£")
        money_str = money_str.replace(",", "")
        return Decimal(money_str)

    money_pattern = r"£\d{1,3}([,]\d{3})*(\.?\d+)?"
    # Due to the way findall works (returning a list of tuple representing groups in each match), we have to
    # make the pattern a match group
    money = re.findall(f"({money_pattern})", amount_str)
    if len(money) == 1:
        return fixed_point(money[0][0])
    else:
        total = re.search(f"total value ({money_pattern})", amount_str)
        if total is not None:
            return fixed_point(total.group(1))
        else:
            print(amount_str)


def extract_date(date_str: str) -> Union[date, Tuple[date, date]]:
    date_format = "%d %B %Y"

    day_range = re.match(r"(\d\d?)-(\d\d?) ([A-Z].+)", date_str)
    if day_range is not None:
        # if it's e.g. 3-5 October 2021
        start = f"{day_range.group(1)} {day_range.group(3)}"
        end = f"{day_range.group(2)} {day_range.group(3)}"
        return datetime.strptime(start, date_format), datetime.strptime(end, date_format)

    # special corrections
    date_str = date_str.removesuffix(" (start date of loan)")
    if date_str == "22 November 20201":  # James Wild's 16 December 2021 entry
        date_str = "22 November 2021"

    try:
        d = datetime.strptime(date_str, date_format)
    except ValueError as e:
        date_range = re.match(r"(.+) (?:–|-|(?:to)) (.+)", date_str)
        if date_range is not None:
            # if it's e.g. 3 October 2021 - 5 October 2021
            start = datetime.strptime(date_range.group(1), date_format)
            end = datetime.strptime(
                date_range.group(2),
                date_format)
            return start, end
        else:
            raise e
    return d


def parse_entry(gift_entries: List[str]):
    pattern = re.compile(
        r"Name of donor: (.*)\nAddress of donor: (.*)\nAmount of donation,? or nature and value if (?:donation|benefit) in kind: (.*)\nDate received: (.*)\nDate accepted: (.*)\nDonor status: (.*)\n")
    for gifts in gift_entries:
        gifts, _ = strip_registration_date(gifts)
        matches = pattern.match(gifts)
        if matches is not None:
            name = matches.group(1)
            address = matches.group(2)
            content = matches.group(3)
            value = extract_value(matches.group(3))
            date_received = extract_date(matches.group(4))
            date_accepted = extract_date(matches.group(5))
            donor_type = matches.group(6)

            gift = Gift(name, address, content, value, date_received, date_accepted, donor_type)
        else:
            pass
            # print(gifts)


if __name__ == "__main__":
    parser.parse({"3. Gifts, benefits and hospitality from UK sources": parse_entry})
