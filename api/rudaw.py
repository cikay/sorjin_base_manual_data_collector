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
        fieldnames = ["title", "url", "text"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        fetch_article_content(writer)


def fetch_article_content(writer):
    max_page = 1000
    current_page = 1
    while True:
        response = requests.get(URL.format(current_page))
        if response.status_code != 200:
            print(f"Failed to retrieve page {current_page}: {response.status_code}")
            raise Exception(
                f"Failed to retrieve page {current_page}: {response.status_code}"
            )

        data = response.json()
        max_page = data["Data"]["MaxPage"]

        articles = []
        for article in data["Data"]["CategoryNews"]["Articles"]:
            articles.append(
                {
                    "title": article["Title"],
                    "url": article["Link"],
                    "text": article["BodyStripped"],
                }
            )

        writer.writerows(articles)
        print("Page {}: {} articles".format(current_page, len(articles)))

        if current_page == max_page:
            print("Reached the last page.")
            break

        current_page += 1
        time.sleep(10)


if __name__ == "__main__":
    fetch_articles()
