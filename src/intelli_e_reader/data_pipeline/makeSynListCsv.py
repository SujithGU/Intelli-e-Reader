import synonymsScraper as ss
import pandas as pd
import time
from pathlib import Path
import json

# Gets path to the root directory of the repository.
parentDirPath = Path(__file__).parent.parent
scraper_obj = ss.Scraper()


wordlist_data = pd.read_csv(
    str(parentDirPath) + '/data/WordsTeachersAverage.csv')
with open(str(parentDirPath) + '/data/AcronymAbbr.json', 'r') as jsonFile:
    pos_dict = json.load(jsonFile)
# Reduces data for levels > A
difficult_wordlist = wordlist_data[wordlist_data['Teachers Avg'] >= 2]


start_time = time.time()
extracted_els = []
count = 0
for index, row in difficult_wordlist.iterrows():
    syns = scraper_obj.find_syns(row.Word)
    if len(syns) > 0:
        try:
            dict1 = {
                'Word': row.Word + '_' + pos_dict[row.PoS],
                'Synonyms': syns
            }
        except KeyError:
            # To handle NaN.
            dict1 = {
                'Word': row.Word + '_' + 'na',
                'Synonyms': syns
            }
        count += 1
        extracted_els.append(dict1)
    print(f'{count} of {len(difficult_wordlist)} completed ', end='\r')

df = pd.DataFrame(extracted_els)
df.to_csv('WordsSynListNew.csv', index=False)
print(f'\n Time taken: {time.time() - start_time}s')
