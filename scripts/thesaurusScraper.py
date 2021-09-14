import csv
from bs4 import BeautifulSoup
import requests


class ThesaurusScraper:
    def make_url(self, search_word):
        template = 'https://www.thesaurus.com/browse/{}?s=t'
        url = template.format(search_word)
        return url

    # Function to retrieve the synonyms through scraping the appropriate classes.
    def scrape_syns(self, soup_obj):

        words = soup_obj.find_all('div', {'class': 'e15rdun50'})
        if len(words) > 0:
            # make syn lists
            # most_relevant_syns = list()
            # moderately_relevant_syns = list()
            # least_relevant_syns = list()
            syn_list = list()

            # Populate lists
            for item in words:
                highSyn = item.find_all('a', {'class': 'css-1kg1yv8'})
                if len(highSyn) > 0:
                    for syn in highSyn:
                        syn_list.append(
                            syn.text.rstrip())

                medSyn = item.find_all('a', {'class': 'css-1gyuw4i'})
                if len(medSyn) > 0:
                    for syn in medSyn:
                        syn_list.append(
                            syn.text.rstrip())

                lowSyn = item.find_all('a', {'class': 'css-1n6g4vv'})
                if len(lowSyn) > 0:
                    for syn in lowSyn:
                        syn_list.append(
                            syn.text.rstrip())

            # return most_relevant_syns, moderately_relevant_syns, least_relevant_syns
            return syn_list
        else:
            print('No words found')

    # Function to be called from another module.

    def find_syns(self, search_word):

        # most_relevant = list()
        # moderately_relevant = list()
        # least_relevant = list()

        html_data = requests.get(self.make_url(search_word))
        soup = BeautifulSoup(html_data.text, 'html.parser')
        syns = self.scrape_syns(soup)
        # most_relevant, moderately_relevant, least_relevant = self.scrape_syns(
        #     soup)

        # if len(most_relevant) > 0:
        #     return_value = most_relevant
        # elif len(moderately_relevant) > 0:
        #     return_value = moderately_relevant
        # else:
        #     return_value = least_relevant
        # return return_value

        # return (most_relevant, moderately_relevant, least_relevant)
        return syns
