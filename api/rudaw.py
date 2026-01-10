import requests
import csv
import time
import re
import os


URL = "https://www.rudaw.net/API/News/Listing/?lang=Kurmanci&CurrentPage={}"
CSV_FILENAME = ".collected_data/news/rudaw.csv"


def fetch_articles():
    file_exists = os.path.exists(CSV_FILENAME)
    with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "url", "content"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            start_page = 1
            writer.writeheader()
        else:
            start_page = 1148

        fetch_article_content(writer, start_page)


def fetch_article_content(writer, start_page=1):
    max_page = 1590
    for page in range(start_page, max_page + 1):
        response = requests.get(URL.format(page))
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: {response.status_code}")
            raise Exception(f"Failed to retrieve page {page}: {response.status_code}")

        data = response.json()

        articles = []
        for article in data["Data"]["CategoryNews"]["Articles"]:
            articles.append(
                {
                    "title": article["Title"],
                    "url": article["Link"],
                    "content": article["BodyStripped"],
                }
            )

        writer.writerows(articles)
        print("Page {}: {} articles".format(page, len(articles)))

        page += 1
        time.sleep(3)


if __name__ == "__main__":
    fetch_articles()
