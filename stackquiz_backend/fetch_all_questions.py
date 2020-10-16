import requests

import itertools
import json
from pathlib import Path
import time

API_URL = "https://api.stackexchange.com/2.2"


def unescape_html(s):
    html_map = {"&#39;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<", "&amp;": "&"}

    for fr, to in html_map.items():
        s = s.replace(fr, to)

    return s


def collect_sites():
    site_file = Path("data/sites.json")
    if site_file.exists():
        print("Already collected sites")
        return

    sites = []
    for page in itertools.count(1):
        r = requests.get(
            f"{API_URL}/sites?page={page}&pagesize=100&filter=!Fn4IA0AkIga(j1fOyW2WTVuPn2"
        )
        site_data = r.json()
        for site in site_data["items"]:
            if site["site_type"] == "main_site":
                sites.append(
                    {
                        "name": site["name"],
                        "api_name": site["api_site_parameter"],
                        "site": site["site_url"],
                        "logo": site["logo_url"],
                        "icon": site["icon_url"],
                        "icon_hr": site["high_resolution_icon_url"],
                    }
                )

        if not site_data["has_more"]:
            break

        time.sleep(1 / 20)  # throttling

    with open(site_file, "w") as f:
        json.dump({"sites": sorted(sites, key=lambda x: x["api_name"])}, f)


def collect_questions():
    progress_file = Path("data/progress.json")
    site_list_file = Path("data/sites.json")

    with open(site_list_file) as f:
        sites = [site["api_name"] for site in json.load(f)["sites"]]

    if progress_file.exists():
        with open(progress_file) as f:
            progress = json.load(f)
    else:
        progress = {"site": 0, "page": 1, "done": False}
        with open(progress_file, "w") as f:
            json.dump(progress, f)

    if progress["done"]:
        print("Already finished collecting questions.")
        return

    site_data = None

    try:
        for site_index in itertools.count(progress["site"]):
            if site_index == len(sites):
                progress["done"] = True
                with open(progress_file, "w") as f:
                    json.dump(progress, f)

                print("Finished!")
                return

            progress["site"] = site_index

            site = sites[site_index]
            print(f"Pulling from {site}")
            site_file = Path(f"data/{site}.json")
            if site_file.exists():
                with open(site_file) as f:
                    site_data = json.load(f)

            else:
                site_data = {"questions": []}

            for page in itertools.count(progress["page"]):
                print(f"Page {page}")
                r = requests.get(
                    f"{API_URL}/questions?page={page}&pagesize=100&order=desc&sort=activity&site={site}&filter=!-MOq2dN6MT9z*aszmf-RU_S6JslA4pKhf"
                )
                if r.status_code != 200:
                    print(f"Request status code: {r.status_code}")
                    with open(progress_file, "w") as f:
                        json.dump(progress, f)

                    with open(site_file, "w") as f:
                        json.dump(site_data, f)

                q_data = r.json()
                for question in q_data["items"]:
                    site_data["questions"].append(
                        {
                            "link": question["link"],
                            "title": unescape_html(question["title"]),
                        }
                    )

                progress["page"] = page + 1

                if q_data["quota_remaining"] == 0:
                    print("Exhausted quota!")
                    with open(progress_file, "w") as f:
                        json.dump(progress, f)

                    with open(site_file, "w") as f:
                        json.dump(site_data, f)

                    return

                print(f"Quota left: {q_data['quota_remaining']}")
                sleep_time = q_data.get("backoff", 1)
                print(f"Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)

                if not q_data["has_more"]:
                    print(f"Finished {site}")
                    site_data["total_questions"] = q_data["total"]
                    with open(site_file, "w") as f:
                        json.dump(site_data, f)

                    break

            progress["page"] = 1

    except KeyboardInterrupt:
        print("Interrupted")
        with open(progress_file, "w") as f:
            json.dump(progress, f)

        with open(site_file, "w") as f:
            json.dump(site_data, f)


if __name__ == "__main__":
    collect_sites()
    collect_questions()
