import requests

import itertools
import json
from pathlib import Path
import time

API_URL = "https://api.stackexchange.com/2.2"


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

        time.sleep(1 / 30)  # throttling

    with open(site_file, "w") as f:
        json.dump({"sites": sites}, f)


if __name__ == "__main__":
    collect_sites()
