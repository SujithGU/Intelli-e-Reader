import pandas as pd
import logging
import os
import sys

if not os.path.exists('../Data Files/logs'):
    os.mkdir('../Data Files/logs')

logging.basicConfig(filename='../Data Files/logs/fetch_cefr_log_file.log',
                    filemode='w',
                    level=logging.DEBUG)


class Cefr:
    try:
        # Read the potential csv file
        df = pd.read_csv("../Data Files/word_pos_modified_data.csv")
        logging.debug("Data read success")

        # Consisting of word + part of speech combination as key and cefr level as value
        word_pos_dict = dict()

        # Conversion map for part of speech
        conversion_map = {'DET': 'dt', 'VERB': 'v', 'NOUN': 'n', 'ADJ': 'aj', 'ADV': 'av', 'PRONOUN': 'pn', 'ADP': 'pp',
                          'CONJ': 'cj'}
        df['wor_pos_map'] = df['pos'].replace(conversion_map)

        for row_index in df.index:
            combine = df['word'][row_index].lower() + "_" + df['wor_pos_map'][row_index]
            word_pos_dict[combine] = df['cefr_level'][row_index]

        def getCefr(self='no arg', part_of_speech='no arg'):
            """
            Use this method in order to receive the CEFR level of the word and part of speech combination
            :param self: word
            :param part_of_speech: part of speech of the word
            :return: reduced cefr level
            """
            word = str(self).lower()
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

    except:
        logging.error("Read Error ", sys.exc_info())

