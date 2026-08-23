"""
Script to generate ngram information from start-year-end year for
a given data set of Word and PoS

"""

import pandas as pd
from config import Config
from intelli_e_reader.data_pipeline.google_ngram_parser import get_ngram_data


class NgramGenerator:

    def __init__(self, file_location=None, word_string=None, pos_string=None,save_location=None):
        self.df = pd.read_csv(file_location)
        self.word_list = self.df[word_string]
        self.pos_list = self.df[pos_string]
        self.save_location = save_location

    def generate_ngram_data(self, start=2013, end=2019):
        list_of_years = list(range(start, end + 1))
        list_of_ngrams = []
        year_index = 0
        while year_index == len(list_of_years):
            year = list_of_years[year_index]
            for index, word in enumerate(self.word_list):
                print(f'Parsing Index - {index + 1}')
                list_of_ngrams.append(get_ngram_data(word=word, pos=self.pos_list[index], year=year))

            self.df[f'ngram_{year}'] = list_of_ngrams
            year_index += 1

    def save_data(self):
        self.df.to_csv(self.save_location, index=False)


if __name__ == '__main__':

    ngram = NgramGenerator(file_location=f'{Config.PROCESSED_DATA_FOLDER}/master_cefr.csv',
                           word_string='word',
                           pos_string='pos',
                           save_location=f'{Config.PROCESSED_DATA_FOLDER}/master_cefr_with_ngram.csv')

    ngram.generate_ngram_data()
    ngram.save_data()
