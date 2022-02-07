import json

import lark
from lark.lark import Lark


def try_parse(parser: Lark, lines: list[str]):
    successful = []
    failed = []
    for line in lines:
        try:
            parser.parse(line)
        except lark.UnexpectedCharacters:
            failed.append(line)
        else:
            successful.append(line)

    return successful, failed


if __name__ == "__main__":
    with open("crawler/interests.json", "r", encoding="utf-8") as interests_f:
        interests: dict = json.load(interests_f)

    lines = {
        "heading": [],
        "sub": [],
        "naked": []
    }

    for member_entry in interests.values():
        e_and_e = member_entry.get("1. Employment and earnings")
        if e_and_e is not None:
            for block in e_and_e:
                if isinstance(block, dict):
                    heading, sub = list(block.items())[0]
                    lines["heading"].append(heading)
                    lines["sub"].extend(sub)
                elif isinstance(block, str):
                    lines["naked"].append(block)
                else:
                    raise ValueError(f"invalid entry type: {block}")

    overall_count = 0
    success_count = 0
    for typ, grammar_file in {"naked": "grammars/payment.lark",
                              "heading": "grammars/payment_header.lark",
                              "sub": "grammars/payment_sub.lark"
                              }.items():
        with open(grammar_file, "r") as grammar:
            parser = Lark(grammar, debug=True)
            success, fail = try_parse(parser, lines[typ])

            overall_count += len(lines[typ])
            success_count += len(success)

            print(
                f"{typ}: {len(lines[typ])} total, {len(success)} successful, {len(fail)} failed, success rate {len(success) / len(lines[typ]):.2f}")

            with open(f"failures/{typ}.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(fail))

    print(f"{overall_count} total, success rate {success_count / overall_count:.2f}")
