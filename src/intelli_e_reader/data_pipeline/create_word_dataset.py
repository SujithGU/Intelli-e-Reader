import pandas as pd
import json
import nltk

from config import Config


class Tagger:
    def __init__(self, file=None, save_location=None):
        nltk.download('averaged_perceptron_tagger')

        # Mapping between NLTK POS TAG to Google Ngram Tag
        self.ngram_tag_dictionary = {'CC': 'CONJ', 'IN': 'CONJ', 'CD': '',
                                     'DT': 'DET', 'JJ': 'ADJ', 'JJR': 'ADJ',
                                     'JJS': 'ADJ', 'MD': '', 'NN': 'NOUN', 'NNS': 'NOUN',
                                     'NNP': 'NOUN', 'NNPS': 'NOUN', 'PRP': 'PRON', 'PRP$': 'PRON',
                                     'RB': 'ADV', 'RBR': 'ADV', 'RBS': 'ADV', 'TO': '',
                                     'VB': 'VERB', 'VBD': 'VERB', 'VBG': 'VERB', 'VBN': 'VERB', 'VBZ': 'VERB',
                                     'VBP': 'VERB', 'WDT': '', 'WP': '', 'WP$': '', 'WRB': '','EXC':''}
        self.file_location = file
        self.save_location = save_location
        self.df = None
        with open(self.file_location, 'r') as f:
            self.data = json.load(f)

    def read_and_tag(self):
        word_list = list(self.data.keys())
        self.df = pd.DataFrame(data=word_list, columns=['eng_words'])

        list_of_pos = []

        index = 0

        for word in word_list:
            pos = nltk.pos_tag([word])[0][1]
            list_of_pos.append(pos)
            index += 1
            print(f'Tagging Word Number  - {index}')

        self.df['pos_tag'] = list_of_pos
        self.df['pos_tag'] = self.df['pos_tag'].map(self.ngram_tag_dictionary)

    def save_file(self):
        # Save csv format
        self.df.to_csv(self.save_location, index=False)


if __name__ == '__main__':

    tagger = Tagger(file=f'{Config.DATA_FOLDER}/all_english_words.json',
                    save_location=f'{Config.DATA_FOLDER}/all_english_words_tagged.csv')
    tagger.read_and_tag()
    tagger.save_file()
