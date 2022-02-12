import re
from typing import List, Union

import lark
from lark.lark import Lark

import parser
from utils import strip_registration_date

ambig = 0


def strip_late(entry: str) -> str:
    pattern = re.compile("This is a late .+")
    return pattern.sub("", entry)


def try_parse(parser: Lark, lines: list[str]):
    successful = []
    failed = []
    for line in lines:
        line, _ = strip_registration_date(line)
        line = strip_late(line)
        try:
            t = parser.parse(line)
            if t.data == "_ambig":
                global ambig
                ambig += 1
        except lark.UnexpectedCharacters:
            failed.append(line)
        except Exception as e:
            print(line)
            raise e
        else:
            successful.append(line)

    return successful, failed


lines = {
    "heading": [],
    "sub": [],
    "naked": []
}


def parse_entry(employment_earning_entries: List[Union[dict, str]]):
    for entry in employment_earning_entries:
        if isinstance(entry, dict):
            heading, sub = list(entry.items())[0]
            lines["heading"].append(heading)
            lines["sub"].extend(sub)
        elif isinstance(entry, str):
            lines["naked"].append(entry)
        else:
            raise ValueError(f"invalid entry type: {entry}")


if __name__ == "__main__":
    parser.parse({"1. Employment and earnings": parse_entry})

    overall_count = 0
    success_count = 0
    for typ, grammar_file in {"naked": "grammars/payment.lark",
                              "heading": "grammars/payment_header.lark",
                              "sub": "grammars/payment_sub.lark"
                              }.items():
        with open(grammar_file, "r") as grammar:
            parser = Lark(grammar, debug=True, ambiguity="explicit")
            success, fail = try_parse(parser, lines[typ])

            overall_count += len(lines[typ])
            success_count += len(success)

            print(
                f"{typ}: {len(lines[typ])} total, {len(success)} successful, {len(fail)} failed, success rate {len(success) / len(lines[typ]):.3f}")

            with open(f"failures/{typ}.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(fail))

    print(f"{overall_count} total, success rate {success_count / overall_count:.3f}")
    print(ambig)
