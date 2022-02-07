import json

from bs4 import BeautifulSoup
import requests

session = requests.Session()


# Mapping from name to individual member's page link
def gen_directory():
    links = {}

    directory_page = session.get("https://publications.parliament.uk/pa/cm/cmregmem/220131/contents.htm").text
    soup = BeautifulSoup(directory_page, "html.parser")
    main_block = soup.find(id="mainTextBlock")
    ps = main_block.select("p")[3:]
    for p in ps:
        name = p.a.text.strip()
        link = f"https://publications.parliament.uk/pa/cm/cmregmem/220131/{p.a['href']}"
        links[name] = link

    return links


def get_interests(link: str) -> dict:
    member_page = session.get(link).text

    soup = BeautifulSoup(member_page, "html.parser")
    main_block = soup.find(id="mainTextBlock")
    ps = main_block.select("p")[1:]

    parsed = {}
    cur_nodes = []
    for p in ps:
        classes = p.attrs.get("class")
        if classes is None and p.strong is not None and p.strong.text != "Nil":
            cur_nodes = []
            parsed[p.strong.text] = cur_nodes
        elif classes is not None:
            if classes[0] == "indent":
                cur_nodes.append(p.get_text("\n"))
            elif classes[0] == "indent2":
                heading = cur_nodes[-1]
                if isinstance(heading, str):
                    cur_nodes[-1] = {heading: [p.get_text("\n")]}
                else:
                    heading[list(heading.keys())[0]].append(p.get_text("\n"))
            elif classes[0] == "spacer":
                pass
            else:
                print(f"Failed to crawl on {link}: {p}")
    return parsed


def populate_interests():
    interests = {}
    members = gen_directory()
    from tqdm import tqdm

    for name, link in tqdm(members.items()):
        interest = get_interests(link)
        if interest != "":
            interests[name] = interest
    with open("interests.json", "w", encoding="utf-8") as f:
        json.dump(interests, f, ensure_ascii=False)


if __name__ == "__main__":
    populate_interests()
