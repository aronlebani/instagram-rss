#!/usr/local/bin/python3

import rssmerger
import igscraper
import dotenv
import pickle
import glob
import os

def has_scraped_users():
    username = os.getenv("IG_USERNAME")
    dirname = "./exports/" + username
    return len(os.listdir(dirname)) > 0

def get_users_from_file():
    username = os.getenv("IG_USERNAME")
    file_glob = "./exports/" + username + "/*.pkl"
    list_of_files = glob.glob(file_glob)
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, "rb") as f:
        data = pickle.load(f)
    return data

def scrape_users():
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    igscraper.scrape("following", username, password) 

def get_profile_stub(url):
    return url.replace("www.", "").replace("https://instagram.com/", "").replace("/", "")

def get_rss_url(url):
    stub = get_profile_stub(url)
    rsshub_url = os.getenv("RSSHUB_URL")
    return rsshub_url + "/picuki/profile/" + stub

def main():
    dotenv.load_dotenv()

    if not has_scraped_users():
        scrape_users()

    users = get_users_from_file()

    rss_urls = {}
    for index, url in enumerate(users):
        rss_urls[get_profile_stub(url)] = get_rss_url(url)

    # Use these for testing
    # rss_urls = {
    #     "surprisechef": get_rss_url("surprisechef"),
    #     "karateboogaloo": get_rss_url("karateboogaloo")
    # }

    rssmerger.combine(rss_urls)

if __name__ == "__main__":
    main()
