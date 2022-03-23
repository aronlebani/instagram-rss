import pickle
import dotenv
import os

dotenv.load_dotenv()

def get_profile_stub(url):
    return url.replace("www.", "").replace("https://instagram.com/", "").replace("/", "")

def get_rss_url(url):
    stub = get_profile_stub(url)
    rsshub_url = os.getenv("RSSHUB_URL")
    return rsshub_url + "/picuki/profile/" + stub

with open("exports/aronlebani/following2022-01-15T21:57:13.pkl", "rb") as file:
    data = pickle.load(file)

following = []
for url in data:
    rss_url = get_rss_url(url)
    following.append(rss_url)

with open("exports/aronlebani/following2022-01-15T21:57:13.txt", "w") as file:
    file.writelines("%s\n" % x for x in following)
