import thesaurusScraper as ts
import pandas as pd
import time

wordlist_data = pd.read_csv('/Users/prajyotsuvarna/Documents/College/Programming/word-level-survey/WordsTeachersAverage.csv')
# Reduces data for levels > A
difficult_wordlist = wordlist_data[wordlist_data['Teachers Avg'] >= 2]

start_time = time.time()
extracted_els = []
count = 0
for index, row in difficult_wordlist.iterrows():
    syns = ts.retrieve_syns(row.Word)
    dict1 = {
         'Word': row.Word,
         'Synonyms': syns
    }
    count += 1
    extracted_els.append(dict1)
    print(f'{count} of {len(difficult_wordlist)} completed ', end='\r')

df = pd.DataFrame(extracted_els)
df.to_csv('WordsSynList.csv', index=False) 
print(f'\n Time taken: {time.time() - start_time}s')