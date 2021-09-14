from os import system
import spacy
import pandas as pd
import json
from pathlib import Path

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


class TestCefrLevel:

    def __init__(self) -> None:
        self.nlp = spacy.load('en_core_web_md')

    def read_file(self, filePath):
        try:
            self.master_cefr = pd.read_csv(filePath)
        except:
            print('Error in retrieving file - mastercefr')
        finally:
            self.master_cefr_A = self.master_cefr[self.master_cefr['cefr'] == 'A']
            self.master_cefr_B = self.master_cefr[self.master_cefr['cefr'] == 'B']
            self.master_cefr_C = self.master_cefr[self.master_cefr['cefr'] == 'C']

    def rank_syns(self, orig_word, synList):

        # Lemmatization
        # lemmatizer = WordNetLemmatizer()

        # new_syns
        # new_syns = set()
        # for i in range(len(synList)):
        #     words = nltk.word_tokenize(synList[i])
        #     # lemmatize if it's not a stop word
        #     words = [lemmatizer.lemmatize(word) for word in words if word not in set(
        #         stopwords.words('english'))]
        #     new_syns.add(words[0])

        doc1 = self.nlp(orig_word)
        word_distances = []
        for syn in synList:
            doc2 = self.nlp(syn)
            distance = doc1.similarity(doc2)
            word_distances.append((syn, distance))

        word_distances.sort(key=lambda x: x[1], reverse=True)
        return word_distances
