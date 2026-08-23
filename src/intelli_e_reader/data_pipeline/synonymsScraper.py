import csv
from bs4 import BeautifulSoup
import requests
import time


class Scraper:

    def make_url(self, search_word):
        template = 'https://www.synonyms.com/synonym/{}'
        url = template.format(search_word)
        return url

    def get_syns(self, soup_obj, search_word):

        synList = []
        sections = soup_obj.find_all('div', {'class': 'rc5'})

        for section in sections:
            paraphrases = section.find('p', {'class': 'term'})
            if paraphrases and paraphrases.string == 'List of paraphrases for "' + search_word + '":':
                # Find the parent tag.
                parent = paraphrases.parent

                # Navigate to syn tag and extract the synonyms.
                syn_tag = parent.find('p', {'class': 'syns'})
                syn_links = syn_tag.find_all('a')
                for syn in syn_links:
                    synList.append(syn.string)
                break

        return synList

    def find_syns(self, search_word):

        html_data = requests.get(self.make_url(search_word))
        soup = BeautifulSoup(html_data.text, 'html.parser')
        synonyms = self.get_syns(soup, search_word)
        return synonyms
