import ast

import pandas as pd

from config import Config


class SynRetriever:

    def __init__(self):
        # Reads the raw sources directly (was ThesaurusDict.json +
        # SynonymsDict.json, built by data_pipeline/csvToJson.py from the
        # same two files). Deliberately NOT using data_utils.py's
        # family2_word_synonyms.parquet here: that table precomputes the
        # combined candidate list for one specific (word, word's-own-pos)
        # pair, which loses the synonym-scraper source's actual semantics --
        # its candidates apply to a word regardless of which POS it's used
        # as, not just the POS recorded in the CEFR dataset. Keeping the two
        # sources separate and unioning them per-query, like the original,
        # preserves that.
        try:
            synonyms = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/synonyms_scrape.csv").rename(
                columns={"Word": "word", "Synonyms": "synonym_list"})
            thesaurus = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/thesaurus_scrape.csv").rename(
                columns={"Word": "word", "Synonyms": "synonym_list"})
            synonyms["synonym_list"] = synonyms["synonym_list"].apply(ast.literal_eval)
            thesaurus["synonym_list"] = thesaurus["synonym_list"].apply(ast.literal_eval)

            # word (pos-agnostic) -> candidates
            self.syn_json = dict(zip(synonyms["word"].str.lower(), synonyms["synonym_list"]))
            # word_pos, e.g. "absolute_aj" (thesaurus_scrape.csv's own short-acronym
            # POS suffix, already in this form) -> candidates
            self.thes_json = dict(zip(thesaurus["word"].str.lower(), thesaurus["synonym_list"]))
        except Exception:
            print('Error in retrieving file')
            self.syn_json = {}
            self.thes_json = {}

    def retrieveSynsByPos(self, word, Pos):
        """Functions retrieves only synonyms for PoS from both sources

        Args:
            word (string): Word to be found
            Pos (string): Parts of speech of the word

        Returns:
            [string]: Returns the synonyms of the word
        """
        thes_list = self.thes_json.get(word + '_' + Pos)
        if thes_list is None:
            thes_list = []

        syn_list = self.syn_json.get(word)
        if syn_list is None:
            syn_list = []

        comb_list = thes_list + syn_list
        if len(comb_list) > 0:
            comb_list = self.refactor_list(comb_list)

        return comb_list

    def retrieveAllSyns(self, word):
        """Function retrieves synonyms for all PoS's

        Args:
            word (string): Word to be found

        Returns:
            [string]: Returns all the synonyms of the word
        """
        possible_pos = ['n', 'v', 'av', 'na', 'aj', 'pp', 'pn']
        syn_list = self.syn_json.get(word)
        if syn_list is None:
            syn_list = []

        cumulative_list = list()
        for pos in possible_pos:
            pos_word = word + '_' + pos
            syns = self.thes_json.get(pos_word)
            if syns is not None:
                cumulative_list += syns

        if len(cumulative_list) > 0:
            cumulative_list = self.refactor_list(cumulative_list)

        return cumulative_list

    def refactor_list(self, oldList):
        """Method to refactor the lsit of duplicates and unwanted spaces.

        Args:
            oldList ([string]): List to be refactored.

        Returns:
            [string]: Refactored list.
        """
        # Get unique list from the combination.
        oldList = list(dict.fromkeys(oldList))
        # Removes spaces before words.
        return list(map(str.lstrip, oldList))
