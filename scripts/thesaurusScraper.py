import csv
from bs4 import BeautifulSoup
import requests
from selenium import webdriver

def make_url(search_word):
    template = 'https://www.thesaurus.com/browse/{}?s=t'
    url = template.format(search_word)
    return url

# Function to retrieve the synonyms through scraping the appropriate classes.
def scrape_syns(soup_obj):
    
    words = soup_obj.find_all('div', {'class': 'etbu2a30'})
    
    # make syn lists
    most_relevant_syns = list()
    moderately_relevant_syns = list()
    least_relevant_syns = list()
    
    # Populate lists
    for item in words:
        highSyn = item.find('a', {'class' : 'css-1m14xsh'})
        if highSyn:
            most_relevant_syns.append(item.find('a', {'class' : 'css-1m14xsh' }).text.rstrip())
        
        medSyn = item.find('a', {'class' : 'css-y8q7q9' })
        if medSyn:
            moderately_relevant_syns.append(item.find('a', {'class' : 'css-y8q7q9' }).text.rstrip())
            
        lowSyn = item.find('a', {'class' : 'css-1irfus7' })
        if lowSyn:
            least_relevant_syns.append(item.find('a', {'class' : 'css-1irfus7' }).text.rstrip())

    return most_relevant_syns, moderately_relevant_syns, least_relevant_syns

# Function to be called from another module.    
def retrieve_syns(search_word):

    most_relevant = list()
    moderately_relevant = list()
    least_relevant = list()

    html_data = requests.get(make_url(search_word))
    soup = BeautifulSoup(html_data.text,'html.parser') 
    most_relevant, moderately_relevant, least_relevant = scrape_syns(soup)

    if len(most_relevant) > 0:
        return_value = most_relevant
    elif len(moderately_relevant) > 0:
        return_value = moderately_relevant
    else:
        return_value = least_relevant
    return return_value