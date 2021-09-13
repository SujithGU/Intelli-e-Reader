from bs4 import BeautifulSoup
import requests
import json


def get_ngram_data(word=None, pos=None, year=2013):
    """
    Script to scrape the google ngram viewer for information about a word and its PoS combination
    * If a word_PoS combination yields no response, information of word alone will be fetched.
    * When both the situations yield with no response, a value of 0.000000 will be returned
    """

    # Only a certain amount of PoS are supported by Google Ngram, rest of the PoS will be considered
    # as invalids - https://books.google.com/ngrams/info

    invalids = ['EXC', 'AVB', 'PRONOUN', 'PHR', 'PRON', 'MVB', 'NAN', None]
    if pos not in invalids:
        actual_word = word + "_" + pos
    else:
        actual_word = word

    # Parse URL
    URL = f"https://books.google.com/ngrams/graph?content={actual_word}&year_start={year - 1}&year_end={year}&corpus" \
          f"=26&smoothing=3&case_insensitive=true "

    r = requests.get(URL)
    if r.status_code != 200:
        return 0.000000

    soup = BeautifulSoup(r.content, 'html5lib')
    data = soup.find_all('script')[5].string
    data = (data.split('\n')[2]).replace(';', '').split('=')[1]
    data = json.loads(data)
    for val in data:

        if val['ngram'] == actual_word:
            return round(val['timeseries'][1], 6)
