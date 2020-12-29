from pathlib import Path
import json

class SynRetriever:

    def __init__(self):

        # path to root directory of repo.
        path = str(Path(__file__).parent.parent)
        
        # Retrieve the json data from both the files.
        try:
            with open(path + '/Data Files/ThesaurusDict.json') as thes_json_file:
                self.thes_json = json.load(thes_json_file)

            with open(path + '/Data Files/SynonymsDict.json') as syn_json_file:
                self.syn_json = json.load(syn_json_file)
        except:
            print('Error in retrieving file')



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
            print(f'For PoS {pos_word} the syns are {syns}\n\n')
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



        


