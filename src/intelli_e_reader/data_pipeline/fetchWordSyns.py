import synonymsScraper as ss
import thesaurusScraper as ts
import pandas as pd
import time
from pathlib import Path
import json


class FetchWordSyns:

    def __init__(self) -> None:
        # Gets path to the root directory of the repository.
        parentDirPath = Path(__file__).parent.parent
        self.scraper_obj = ss.Scraper()
        self.thesaurus_obj = ts.ThesaurusScraper()

        self.level_dict = {
            'A': 1,
            'B': 2,
            'C': 3
        }

        levelA_words = ['chat', 'worry', 'travel',
                        'toast', 'sightseeing', 'journey', 'guide']
        levelB_words = ['acquire', 'ambitious', 'assess', 'breathtaking', 'brief', 'courtesy', 'conjunction',
                        'witty', 'voyage', 'vital', 'trivial', 'sympathy', 'stimulate', 'souvenir', 'queue', 'quarrel', 'parallel']
        levelC_words = ['alliance', 'charisma', 'acquaintance', 'clumsiness', 'catastrophe', 'bias', 'bureaucracy', 'coherence', 'commemorate', 'curb', 'dazzle',
                        'detrimental', 'dispute', 'eccentric', 'eminent', 'envisage', 'facilitate', 'horizon', 'hypocritical', 'impersonal', 'indulge', 'interim', 'juvenile', 'meticulous']

        self.difficult_wordlist = [(levelA_words, 'A'),
                                   (levelB_words, 'B'), (levelC_words, 'C')]

        with open(str(parentDirPath) + '/data/master_cefr.json', 'r') as jsonFile:
            self.master_cefr = json.load(jsonFile)

    def checkSynLevel(self, wordLevel, syns):
        refined_syns = list()
        for syn in syns:
            if self.master_cefr.get(syn) is not None and self.level_dict[self.master_cefr[syn]['cefr']] <= self.level_dict[wordLevel]:
                refined_syns.append(syn)
        return refined_syns

    def main(self, source):
        start_time = time.time()
        extracted_els = []
        for group in self.difficult_wordlist:
            count = 0
            for word in group[0]:
                if source == 'thesaurus':
                    syns = self.thesaurus_obj.find_syns(word)
                elif source == 'synonyms':
                    syns = self.scraper_obj.find_syns(word)
                ref_syns = self.checkSynLevel(group[1], syns)
                if len(ref_syns) > 0:
                    try:
                        dict1 = {
                            'Word': word,
                            'Synonyms': ref_syns,
                            'Level': group[1]
                        }
                    except KeyError:
                        # To handle NaN.
                        dict1 = {
                            'Word': word,
                            'Synonyms': ref_syns,
                            'Level': group[1]
                        }
                    count += 1
                    extracted_els.append(dict1)
                print(f'{count} of {len(group[0])} completed', end='\r')

        df = pd.DataFrame(extracted_els)
        df.to_json('ModelWordsTest_' + source + '.json')
        # df.to_csv('ModelWords_' + source + '.csv', index=False)
        print(f'\n Time taken: {time.time() - start_time}s')
