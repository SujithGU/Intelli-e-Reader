import pandas as pd
import logging
import os

from config import Config


if not os.path.exists(Config.LOG_FOLDER):
    os.makedirs(Config.LOG_FOLDER)

logging.basicConfig(filename=Config.LOG_FOLDER + '/fetch_cefr_log_file.log',
                    filemode='w',
                    level=logging.DEBUG)


class Cefr:
    try:
        # Reads src/intelli_e_reader/data_utils.py's build_family2_synonyms()
        # word_synonyms output (was master_cefr.csv/.json). Only the word/
        # pos/cefr columns are used here -- word_synonyms is a strict
        # superset of the word-CEFR data (same (word, pos) grain, plus a
        # synonym_list column), so there's no separate word-CEFR-only file.
        df = pd.read_parquet(Config.PROCESSED_DATA_FOLDER + "/family2_word_synonyms.parquet",
                             columns=["word", "pos", "cefr"])
        logging.debug("Data read success")

        # Consisting of word + part of speech combination as key and cefr level as value
        word_pos_dict = dict()

        # Set of every known word, for checkWord()
        word_set = set()

        # Conversion map for part of speech. Both "NA" and "NAN" mean "no
        # recorded POS" depending on data source/vintage; map both to 'na'.
        conversion_map = {'DET': 'dt', 'VERB': 'v', 'NOUN': 'n', 'ADJ': 'aj', 'ADV': 'av', 'PRONOUN': 'pn', 'ADP': 'pp',
                          'CONJ': 'cj', 'NAN': 'na', 'NA': 'na'}
        df['wor_pos_map'] = df['pos'].replace(conversion_map)

        for row_index in df.index:
            word_lower = df['word'][row_index].lower()
            combine = word_lower + "_" + df['wor_pos_map'][row_index]
            word_pos_dict[combine] = df['cefr'][row_index]
            word_set.add(word_lower)

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
            return word.lower() in Cefr.word_set

    except:
        logging.error("Read Error")
