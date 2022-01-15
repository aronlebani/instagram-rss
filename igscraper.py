from datetime import datetime
from modules import compare
from modules import file_io
from modules import stats

from modules.scraper import Scraper
from modules.utils import ask_input, ask_multiple_option

def scrape(group, username, password):
    differs = False
    target = username
    scraper = Scraper(target)
    startTime = datetime.now()

    scraper.authenticate(username, password)
    users = scraper.get_users(group, verbose=True)
    scraper.close()

    last_users = file_io.read_last(target, group)
    if last_users:
        differs = bool(compare.get_diffs(users, last_users))

    if (differs or not last_users):
        file_io.store(target, group, users)
    # Stats
    stats.numbers(len(users), scraper.expected_number)
    if (differs): stats.diff(users, last_users)
    print('Took ' + str(datetime.now() - startTime))
