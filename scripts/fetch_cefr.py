import pandas as pd
import logging
import os
import sys
import json
from pathlib import Path


rootPath = str(Path(__file__).parent.parent)
if not os.path.exists(rootPath + '/data_files/logs'):
    os.mkdir(rootPath + '/data_files/logs')
  
# Load the master Cefr file.  
with open(rootPath + '/data_files/master_cefr.json') as json_file:
    master_cefr = json.load(json_file)
    
logging.basicConfig(filename=rootPath + '/data_files/logs/fetch_cefr_log_file.log',
                    filemode='w',
                    level=logging.DEBUG)


class Cefr:
    try:
        # Read the potential csv file
        df = pd.read_csv(rootPath + "/data_files/master_cefr.csv")
        logging.debug("Data read success")

        # Consisting of word + part of speech combination as key and cefr level as value
        word_pos_dict = dict()

        # Conversion map for part of speech
        conversion_map = {'DET': 'dt', 'VERB': 'v', 'NOUN': 'n', 'ADJ': 'aj', 'ADV': 'av', 'PRONOUN': 'pn', 'ADP': 'pp',
                          'CONJ': 'cj', 'NAN': 'na'}
        df['wor_pos_map'] = df['pos'].replace(conversion_map)

        for row_index in df.index:
            combine = df['word'][row_index].lower() + "_" + df['wor_pos_map'][row_index]
            word_pos_dict[combine] = df['cefr'][row_index]

        def getCefr(self, word, part_of_speech):
            """
            Use this method in order to receive the CEFR level of the word and part of speech combination
            :param self: word
            :param word: word
            :param part_of_speech: part of speech of the word
            :return: reduced cefr level
            """
            word = str(word).lower()
            pos = str(part_of_speech).lower()
            logging.debug(f"Requesting for {word} with part of speech {pos} ")

            if word != 'no arg' and pos != 'no arg':
                combo = word + "_" + pos
                ref = Cefr.word_pos_dict.get(combo)
                return ref
            else:
                return None

        def pos_converter(self='', pos='no arg'):
            """
            Use this method to receive the acronym of the part of speech map
            :param: part of speech as received from the data file
            :return: converted acronym for the part of speech
            """
            return Cefr.conversion_map.get(pos.upper())
        
        def checkWord(self, word):
            
            if master_cefr.get(word) is not None:
                return True
            return False

    except:
        logging.error("Read Error")
        # logging.error("Read Error", sys.exc_info())
