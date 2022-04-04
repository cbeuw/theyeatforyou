import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Union

import parser
from utils import strip_registration_date


@dataclass
class Gift:
    donor_name: str
    donor_address: str
    content: str
    value: Decimal
    date_received: Union[date, tuple[date, date]]  # sometimes they give a date range
    date_accepted: date
    donor_type: str


def extract_value(amount_str: str) -> Decimal:
    special_cases = {
        # Greg Smith 21 July 2021
        "Entry with five guests to the Legends Suite at Silverstone to watch the British Grand Prix, value £1,350 (£225 per person)": Decimal(
            "1350"),
        "Entry with one guest to the Fusion Lounge at Silverstone to watch the British Grand Prix, value £1,030 (£515 per person)": Decimal(
            "1030"),
        "Entry with one guest to the Legends Suite at Silverstone to watch the British Grand Prix, value £2,950": Decimal(
            "2950"),
    }

    def fixed_point(money_str: str) -> Decimal:
        money_str = money_str.removeprefix("£")
        money_str = money_str.replace(",", "")
        return Decimal(money_str)

    money_pattern = r"£\d{1,3}(?:[,]\d{3})*(?:\.?\d+)?"
    # Due to the way findall works (returning a list of tuple representing groups in each match), we have to
    # make the pattern a match group
    money = re.findall(f"({money_pattern})", amount_str)
    if len(money) == 1:
        return fixed_point(money[0])

    total = re.search(f"total value ({money_pattern})|({money_pattern}) in total", amount_str)
    if total is not None:
        return fixed_point(total.group(1) if total.group(1) is not None else total.group(2))

    special_parsed = special_cases.get(amount_str)
    if special_parsed is not None:
        return special_parsed
    print(f"Cannot extract money amount: {amount_str}")


def extract_date(date_str: str) -> Union[date, tuple[date, date]]:
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
        date_range = re.match(r"(.+) (?:–|-|to) (.+)", date_str)
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


def parse_entry(gift_entries: list[str]):
    special_cases = {
        # Nickie Aiken 01 November 2021
        "On 22 October 2021, I accepted honorary membership of the Carlton Club for the duration of my time as the MP for the Cities of London and Westminster.":
            Gift(donor_name="Carlton Club", donor_address=None, content="honorary membership", value=None,
                 date_received=None,
                 date_accepted=extract_date("22 October 2021"), donor_type="private members' club"),
        # Sir Iain Duncan Smith
        "I have accepted honorary life membership of Buck’s Club 1919, 18 Clifford Street, London W15 3RF.":
            Gift(donor_name="Buck’s Club", donor_address="18 Clifford Street, London W15 3RF",
                 content="honorary life membership", value=None, date_received=None, date_accepted=None,
                 donor_type="private members' club"),
        "I have accepted honorary life membership of Pratt’s Club as a Special Member, 14 Park Place, London SW1A 1LP.":
            Gift(donor_name="Pratt’s Club", donor_address="14 Park Place, London SW1A 1LP",
                 content="Special Member", value=None, date_received=None, date_accepted=None,
                 donor_type="private members' club"),
        # Kim Leadbeater 06 September 2021
        # FIXME: can we not let this entry surrounded by gentleman's club memberships?
        "Following the murder of my sister, Jo Cox MP, in 2016, Virgin Trains and later LNER have provided myself and my family with a travel permit for use on personal rail journeys. It is not possible to provide an accurate value for this benefit, but it is expected to be worth over £300 a year.":
            Gift(donor_name="Virgin Trains and LNER", donor_address=None,
                 content="travel permit for use on personal rail journeys", value=...,
                 date_received=None, date_accepted=None, donor_type="company"),
        # Jacob Rees-Mogg 25 October 2021
        "On 22 October 2021, I accepted honorary membership of the Carlton Club for the tenure of my position as Leader of the House.":
            Gift(donor_name="Carlton Club", donor_address=None, content="honorary membership",
                 value=None,
                 date_received=None, date_accepted=extract_date("22 October 2021"), donor_type="private members' club"),
        # Mark Spencer 29 November 2021
        "On 2 November 2021, I accepted honorary membership of the Carlton Club for the duration of my tenure as Parliamentary Secretary to the Treasury, and Government Chief Whip.":
            Gift(donor_name="Carlton Club", donor_address=None, content="honorary membership",
                 value=None,
                 date_received=None, date_accepted=extract_date("2 November 2021"), donor_type="private members' club"),
    }
    pattern = re.compile(
        r"Name of donor: (.*)\nAddress of donor: (.*)\nAmount of donation,? or nature and value if (?:donation|benefit) in kind: (.*)\nDate received: (.*)\nDate accepted: (.*)\nDonor status: (.*)")
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
            continue

        if "Carlton Club" in gifts:
            date_match = re.search(r"(?:On|From) (\d\d? [A-Z][a-z]+ \d\d\d\d)", gifts)
            date_accepted = None
            if date_match is not None:
                date_accepted = extract_date(date_match.group(1))

            if re.search(r"honorary membership (of the carlton club )?for life", gifts.lower()) is not None:
                gift = Gift(donor_name="Carlton Club", donor_address=None, content="Honorary Membership for life",
                            value=None,
                            date_received=None, date_accepted=date_accepted, donor_type="private members' club"),
                continue

        if special_cases.get(gifts) is not None:
            gift = special_cases[gifts]
            continue

        print(f"Cannot parse entry: {gifts}")


if __name__ == "__main__":
    parser.parse({"3. Gifts, benefits and hospitality from UK sources": parse_entry,
                  "5. Gifts and benefits from sources outside the UK": parse_entry})
