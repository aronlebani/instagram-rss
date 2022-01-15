import rssmerger
import igscraper
import dotenv
import os

def main():
    dotenv.load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    users = igscraper.scrape("following", username, password) 
    rss_urls = map(lambda index, url: { "item-" + str(index): str(url) }, enumerate(users))
    rssmerger.combine(rss_urls)

if __name__ == "__main__":
    main()
