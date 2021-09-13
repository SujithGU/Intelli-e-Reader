import slate3k as slate
from nltk import pos_tag
import copy
import synRetriever as Syn
import fetch_cefr as cefr
import semanticCheck as sc
from pathlib import Path
import json
import time

class PdfReader:
    
    semantic_check = sc.SemanticCheck()
    modified_sentences = []
    syn = Syn.SynRetriever()
    level = cefr.Cefr()
    rootPath = str(Path(__file__).parent.parent)
    iteration = 0
    highestTracker = list()
        
    def __init__(self):
    
        # Class variables.
        self.load_pdf(self.rootPath)
        
        # Dictionaries for words of different level.
        self.syn_dict_c = {}
        self.syn_dict_b = {}
        self.syn_dict_a = {}

        
    def load_pdf(self, rootPath):
        with open(rootPath + '/data_files/PosAcronym.json') as acryJson:
            self.pos_converter = json.load(acryJson)


    def custom_comp(self, string):
        return string[-1]
    
    
    def get_new_sentence(self, word, part_of_speech, operating_sentence):
        x_word = str(word).replace('[,!?:.;]', '')
        synonym_list = self.syn.retrieveAllSyns(x_word)
        if synonym_list is not None and len(synonym_list) != 0:
            cfr_level = self.level.getCefr(x_word.lower() if part_of_speech != 'np' else x_word[0:-1].lower(),
                                           part_of_speech if part_of_speech != 'np' else 'n')
            part_of_speech = part_of_speech if part_of_speech != 'np' else 'n'
            if cfr_level is not None and cfr_level != 'A':
                synonym_list_a = list()
                synonym_list_b = list()
                synonym_list_c = list()
                # Classifying words in syn lists according to their CEFR's.
                for val in synonym_list:
                    cefr_level_word = self.level.getCefr(val, part_of_speech)
                    if (cefr_level_word is not None) and (ord(cefr_level_word) <= ord(cfr_level)):
                        if cefr_level_word == 'A':
                            synonym_list_a.append(val)
                        elif cefr_level_word == 'B':
                            synonym_list_b.append(val)
                        else:
                            synonym_list_c.append(val)
                    
                if cfr_level == 'C':
                    # get level C
                    if synonym_list_c is not None and len(synonym_list_c) != 0:
                        appended_string_for_c = x_word + "_" + "C"
                        self.syn_dict_c[appended_string_for_c] = synonym_list_c
                    # get Level B
                    if synonym_list_b is not None and len(synonym_list_b) != 0:
                        appended_string_for_b = x_word + "_" + 'B'
                        self.syn_dict_c[appended_string_for_b] = synonym_list_b
                    # get level A
                    if synonym_list_a is not None and len(synonym_list_a) != 0:
                        appended_string_for_a = x_word + "_" + "A"
                        self.syn_dict_c[appended_string_for_a] = synonym_list_a
                elif cfr_level == 'B':
                    # get Level B
                    if synonym_list_b is not None and len(synonym_list_b) != 0:
                        appended_string_for_b = x_word + "_" + 'B'
                        self.syn_dict_b[appended_string_for_b] = synonym_list_b
                    # get level A
                    if synonym_list_a is not None and len(synonym_list_a) != 0:
                        appended_string_for_a = x_word + "_" + "A"
                        self.syn_dict_b[appended_string_for_a] = synonym_list_a
                else:
                    # get level A
                    if synonym_list_a is not None and len(synonym_list_a) != 0:
                        appended_string_for_a = x_word + "_" + "A"
                        self.syn_dict_a[appended_string_for_a] = synonym_list_a
                # Interact with Semantic Check - > Requires Sentence, Word to change , Synonym list and Position
                # of the word
                if len(synonym_list_b) != 0 or len(synonym_list_a) != 0:
                    operating_sentence = self.interact_with_semantic_checker(operating_sentence, x_word, cfr_level,
                                                                        part_of_speech)
                    # self.interact_with_semantic_checker(operating_sentence, x_word, cfr_level,
                    #                                                     part_of_speech)
        return operating_sentence


    def get_new_pos_tagged(self, new_modified_pos_list):
        
        for sentence, list_of_words in new_modified_pos_list:
            print(f"Checking Sentence  '{sentence}' length of words to check= {len(list_of_words)}")
            operating_sentence = copy.deepcopy(sentence)
            for word, part_of_speech in list_of_words:
                # if '-' in word:
                #     if not self.level.checkWord(word) and self.level.checkWord(word.replace('-', '')):
                #         word.replace('-', '')
                operating_sentence = self.get_new_sentence(word, part_of_speech, operating_sentence)
                # self.get_new_sentence(word, part_of_speech, operating_sentence)
            print('Final sentence:', operating_sentence)
            self.modified_sentences.append(operating_sentence)
            print("---------------------------------------------------------------------------------------")
            
            
    def compare_results(self, word, results):
        
        maxScore = 0
        scores = dict()
        # Exxtract scores and the max scores annd max level.
        for key in results.keys():
            level = key.split('_')[1]
            _, score, _ = results[key]
            scores[level] = score
            if score > maxScore:
                maxScore = score
                maxLevel = level
        
        # Compute logic for deep comparision.
        print(scores)
        if self.iteration == 0 or (len(self.highestTracker) > 0 and maxScore > self.highestTracker[1]):
                    
            if scores.get('A') is not None or maxLevel == 'A':
                maxLevel = 'A'
                returnVal = results[word+'_'+'A']
            elif scores.get('B') is not None and maxLevel == 'B':
                returnVal = results[word+'_'+'B']
            elif scores.get('C') is not None and maxLevel == 'C':
                returnVal = results[word+'_'+'C']
            self.appendToHighestTracker(maxLevel, results[word + '_' + maxLevel])
        else:
            pass
            # Highest value was in the previous iteration.
            
            
        return maxLevel, returnVal
        # pass


    def appendToHighestTracker(self, level, *args):
        for index, arg in enumerate(args):
            self.highestTracker[index] = arg
        self.highestTracker[3] = level
        print(self.highestTracker)
        

    def interact_with_semantic_checker(self, sentence, word_to_change, word_cefr_level, parts_of_speech):
        # TODO : Refactor Logic for Deep Semantic check
        results = dict()
        print(f'Word CEFR level is {word_cefr_level}')
        if word_cefr_level == 'C':
            # check self.syn_dict_c first if nothing then check check syn_dict_a
            for character in self.char_range('A', word_cefr_level):
                string_cat = word_to_change + "_" + character
                if string_cat in self.syn_dict_c:
                    list_of_syn = self.syn_dict_c.get(string_cat)
                    if list_of_syn is not None:
                        # best_match = self.get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                        syn,score,new_sent = self.get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                        if score is not None:
                            results[string_cat] = (syn, score, new_sent)
                        # Return
                        # return best_match

        elif word_cefr_level == 'B':
            # check only self.syn_dict_b
            for character in self.char_range('A', word_cefr_level):
                string_cat = word_to_change + "_" + character
                if string_cat in self.syn_dict_b:
                    list_of_syn = self.syn_dict_b.get(string_cat)
                    if list_of_syn is not None:
                        # best_match = self.get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                        syn, score, new_sent = self.get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                        if score is not None:
                            results[string_cat] = (syn, score, new_sent)
                        # Return
                        # return best_match
        else:
            string_cat = word_to_change + "_" + 'A'
            if string_cat in self.syn_dict_a:
                list_of_syn = self.syn_dict_a.get(string_cat)
                if list_of_syn is not None:
                    # best_match = self.get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                    syn,score,new_sent = self.get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                    if score is not None:
                        results[string_cat] = (syn, score, new_sent)
                    # Return
                    # return best_match
        
        if len(results.keys()) > 0:
            (maxLevel, (syn, score, new_sentence)) = self.compare_results(word_to_change, results)
            if maxLevel != 'A' and self.iteration < 1:
                self.iteration += 1
                sentence = self.get_new_sentence(syn, parts_of_speech, new_sentence)
            elif new_sentence != sentence:
                self.iteration = 0 
                print(f'Final word: {syn}')
                sentence = new_sentence
        return sentence


    def char_range(self, c1, c2):
        """Generates the characters """
        for c in range(ord(c1), ord(c2) + 1):
            yield chr(c)


    def get_best_match(self, sentence, word_to_change, list_of_syn, parts_of_speech):
        print(f'Word to be changed is : {word_to_change}')
        print(f"Available Syn : {list_of_syn}")
        print(sentence)
        acceptable_syn = list(self.semantic_check.checkSynPos(sentence, word_to_change, list_of_syn,
                                                        sentence.split().index(word_to_change), parts_of_speech))
        print(f"Acceptable Syn : {acceptable_syn}")
        if (acceptable_syn is not None) and (len(acceptable_syn) > 0):
            match_list = self.semantic_check.calcSemanticScore(sentence, word_to_change, acceptable_syn,
                                                        sentence.split().index(word_to_change))
            # Return
            if match_list is not None and len(match_list) != 0:
                # _, _, sentence = match_list[0]
                word, score, new_sentence = match_list[0]
                return word, round(score, 4), new_sentence
            
        # Return the old sentence.
        return None, None, sentence


    def split_word_cefr(self, word_string):
        list_data = str(word_string).split("_")
        return list_data[0], list_data[1]


    def main(self):
        
        if __name__ == "__main__":
            # new_list = set()
            modified_pos_list = []
            start_time = time.time()
            # Final dictionary to use
            # syn_dict = {}

            # TAG's to exclude as they are conjunctions or Pronouns or words like where,how,what etc
            pos_to_exclude = ['CC', 'CD', 'MD', 'IN', 'NNP', 'NNPS', 'PDT', 'DT', 'PRP', 'PRP$', 'PP', 'RP', 'TO', 'WDT', 'WP', 'WRB']

            # Read PDF
            with open(self.rootPath + '/data_files/pdf/Treasure Island ( PDFDrive )_organized.pdf', 'rb') as f:
                extracted_text = slate.PDF(f)
            # Read Just one page
            pdf = str(extracted_text[0])
            initial_list = pdf.split('.')
            for index, d in enumerate(initial_list):
                initial_list[index] = d.replace("-\n", '').replace('\n', ' ').strip()
                
            print(initial_list)

            # print(f"List of Sentences we are operating on {initial_list}")
            # count = 0
            # for value in initial_list:
            #     # each sentence
            #     word_list = value.split()
            #     tagged = pos_tag(word_list)
            #     list_of_words_to_change = set()
            #     for val1, val2 in tagged:
            #         if val2 not in pos_to_exclude:
            #             list_of_words_to_change.add((val1, self.pos_converter.get(val2)))
            #     modified_pos_list.append((value, list_of_words_to_change))
                # count += 1
                # if count == 3:
                #     break

            # print(f"List of allowed words that we need to work on : {initial_list}")
            # print(f"Modified pos list:\n {modified_pos_list}")
            # self.get_new_pos_tagged(modified_pos_list)
            
            print('Modified sentences:', self.modified_sentences)

            # with open('original.txt', 'w') as f:
            #     for item in initial_list:
            #         f.write("%s\n" % item)
            # with open('modified.txt', 'w') as f:
            #     for item in self.modified_sentences:
            #         f.write("%s\n" % item)

            # print('Total time taken:', time.time() - start_time)
            # print(f"Synonym List for CEFR Level C having only B's : {self.syn_dict_c}")
            # print(f"Synonym List for CEFR Level B having only A's : {self.syn_dict_b}")


obj = PdfReader()
obj.main()
