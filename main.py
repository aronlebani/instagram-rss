import rssmerger
import igscraper

def main():
    username = "test"
    password = "test"
    users = igscraper.scrape("following", username, password) 
    rss_urls = map(lambda index, url: { "item-" + str(index): str(url) }, enumerate(users))
    rssmerger.combine(rss_urls)

if __name__ == "__main__":
    main()
