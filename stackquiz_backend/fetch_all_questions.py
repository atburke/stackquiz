import argparse
import itertools
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

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

        with open(site_file) as f:
            sites = json.load(f)

        return [s["api_name"] for s in sites["sites"]]

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

    sites.sort(key=lambda x: x["api_name"])

    with open(site_file, "w") as f:
        json.dump({"sites": sites}, f)

    return [s["api_name"] for s in sites]


def extract_questions(src, data_dir, tmp_dir=None):
    print(f"Extracting questions from {src}")
    if not tmp_dir:
        tmp_dir = Path("tmp")

    for file in tmp_dir.iterdir():
        file.unlink()

    subprocess.run(["7za", "e", f"-o{str(tmp_dir)}", str(src)], check=True)
    api_name = str(src.name).split(".")[0]
    with open(tmp_dir.joinpath("Posts.xml")) as infile, open(
        data_dir.joinpath(f"{api_name}.txt"), "w"
    ) as outfile:
        for line in infile:
            if line.startswith("  "):
                root = ET.fromstring(line)
                title = root.attrib.get("Title")
                if title:
                    print(title, file=outfile)

    for file in tmp_dir.iterdir():
        file.unlink()

    print(f"Finished {src}")


def port_to_sqlite(data_dir, sites):
    site_map = {site_name: i for i, site_name in enumerate(sites)}
    db_file = data_dir.joinpath("questions.db")
    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()
    if db_file.exists():
        print("Database already exists, resetting")
        c.execute("DELETE FROM data")

    else:
        c.execute(
            "CREATE TABLE data (idx INTEGER NOT NULL PRIMARY KEY, question TEXT, class INTEGER)"
        )

    index = 0
    for file in data_dir.iterdir():
        if file.suffix != ".txt":
            continue

        print(f"Importing {file.stem}, index starting at {index}")

        with open(file) as f:
            for line in f:
                c.execute(
                    f"INSERT INTO data VALUES (?, ?, ?)",
                    (index, line, site_map[file.stem]),
                )
                index += 1

    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src_dir", type=Path)
    args = parser.parse_args()
    sites = collect_sites()
    data_dir = Path("data")
    for file in args.src_dir.iterdir():
        if (
            file.is_file()
            and file.suffix == ".7z"
            and not data_dir.joinpath(f"{file.name.split('.')[0]}.txt").exists()
        ):
            extract_questions(file, data_dir)

    port_to_sqlite(data_dir, sites)
