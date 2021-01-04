import slate3k as slate
from nltk import pos_tag
import copy
import synRetriever as Syn
import fetch_cefr as cefr
import semanticCheck

syn_dict_c = {}
syn_dict_b = {}
syn_dict_a = {}

semantic_check = semanticCheck.SemanticCheck()
modified_sentences = []


def custom_comp(string):
    return string[-1]


def get_new_pos_tagged(new_modified_pos_list):
    for sentence, list_of_words in new_modified_pos_list:
        print(f"Checking Sentence  {sentence} length of words to check= {len(list_of_words)}")
        operating_sentence = copy.deepcopy(sentence)
        for word, part_of_speech in list_of_words:
            x_word = str(word).replace('[,!?:.]', '')
            synonym_list = syn.retrieveSynsByPos(x_word, str(part_of_speech))
            if synonym_list is not None and len(synonym_list) != 0:
                cfr_level = level.getCefr(x_word.lower(), part_of_speech)
                if cfr_level is not None and cfr_level != 'A':
                    synonym_list_a = []
                    synonym_list_b = []
                    synonym_list_c = []
                    for val in synonym_list:
                        cefr_level_word = level.getCefr(val, part_of_speech)
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
                            syn_dict_c[appended_string_for_c] = synonym_list_c
                        # get Level B
                        if synonym_list_b is not None and len(synonym_list_b) != 0:
                            appended_string_for_b = x_word + "_" + 'B'
                            syn_dict_c[appended_string_for_b] = synonym_list_b
                        # get level A
                        if synonym_list_a is not None and len(synonym_list_a) != 0:
                            appended_string_for_a = x_word + "_" + "A"
                            syn_dict_c[appended_string_for_a] = synonym_list_a
                    elif cfr_level == 'B':
                        # get Level B
                        if synonym_list_b is not None and len(synonym_list_b) != 0:
                            appended_string_for_b = x_word + "_" + 'B'
                            syn_dict_b[appended_string_for_b] = synonym_list_b
                        # get level A
                        if synonym_list_a is not None and len(synonym_list_a) != 0:
                            appended_string_for_a = x_word + "_" + "A"
                            syn_dict_b[appended_string_for_a] = synonym_list_a
                    else:
                        # get level A
                        if synonym_list_a is not None and len(synonym_list_a) != 0:
                            appended_string_for_a = x_word + "_" + "A"
                            syn_dict_a[appended_string_for_a] = synonym_list_a
                    # Interact with Semantic Check - > Requires Sentence, Word to change , Synonym list and Position
                    # of the word
                    if len(synonym_list_b) != 0 or len(synonym_list_a) != 0:
                        operating_sentence = interact_with_semantic_checker(operating_sentence, x_word, cfr_level,
                                                                            part_of_speech)
        modified_sentences.append(operating_sentence)
        print("---------------------------------------------------------------------------------------")


def interact_with_semantic_checker(sentence, word_to_change, word_cefr_level, parts_of_speech):
    # TODO : Refactor Logic for Deep Semantic check
    if word_cefr_level == 'C':
        # check syn_dict_c first if nothing then check check syn_dict_a
        for character in char_range('A', word_cefr_level):
            string_cat = word_to_change + "_" + character
            if string_cat in syn_dict_c:
                list_of_syn = syn_dict_c.get(string_cat)
                if list_of_syn is not None:
                    best_match = get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                    # Return
                    return best_match

    elif word_cefr_level == 'B':
        # check only syn_dict_b
        for character in char_range('A', word_cefr_level):
            string_cat = word_to_change + "_" + character
            if string_cat in syn_dict_b:
                list_of_syn = syn_dict_b.get(string_cat)
                if list_of_syn is not None:
                    best_match = get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                    # Return
                    return best_match
    else:
        string_cat = word_to_change + "_" + 'A'
        if string_cat in syn_dict_a:
            list_of_syn = syn_dict_a.get(string_cat)
            if list_of_syn is not None:
                best_match = get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech)
                # Return
                return best_match

    return sentence


def char_range(c1, c2):
    """Generates the characters """
    for c in range(ord(c1), ord(c2) + 1):
        yield chr(c)


def get_best_match(sentence, word_to_change, list_of_syn, parts_of_speech):
    print(f"Available Syn : {list_of_syn}")
    acceptable_syn = list(semantic_check.checkSynPos(sentence, word_to_change, list_of_syn,
                                                     sentence.split().index(word_to_change), parts_of_speech))
    print(f"Acceptable Syn : {acceptable_syn}")
    if (acceptable_syn is not None) and (len(acceptable_syn) > 0):
        match_list = semantic_check.calcSemanticScore(sentence, word_to_change, acceptable_syn,
                                                      sentence.split().index(word_to_change))
        # Return
        if match_list is not None and len(match_list) != 0:
            _, _, sentence = match_list[0]
            return sentence
        else:
            return sentence
    else:
        return sentence


def split_word_cefr(word_string):
    list_data = str(word_string).split("_")
    return list_data[0], list_data[1]


syn = Syn.SynRetriever()
level = cefr.Cefr()
new_list = set()
modified_pos_list = []

# Final dictionary to use
syn_dict = {}

# TAG's to exclude as they are conjunctions or Pronouns or words like where,how,what etc
pos_to_exclude = ['CC', 'CD', 'MD', 'NNP', 'NNPS', 'PDT', 'DT', 'PRP', 'PRP$', 'RP', 'TO', 'WDT', 'WP', 'WRB']

# NLTK tag list -> custom tag for project
pos_converter = {'NN': 'n', 'NNS': 'n', 'VB': 'v', 'VBG': 'v', 'VBD': 'v',
                 'VBN': 'v', 'VBP': 'v', 'VBZ': 'v', 'JJ': 'aj', 'JJR': 'aj', 'JJS': 'aj',
                 'RB': 'av', 'RBR': 'av', 'RBS': 'av', 'IN': 'pp', 'CC': 'cj'}

# Read PDF
with open('../Data Files/pdf/Treasure Island ( PDFDrive )_organized.pdf', 'rb') as f:
    extracted_text = slate.PDF(f)
# Read Just one page
pdf = str(extracted_text[1])
initial_list = pdf.split('.')
for index, d in enumerate(initial_list):
    initial_list[index] = d.replace("-\n", '').replace('\n', ' ').strip()

print(f"List of Sentences we are operating on {initial_list}")

for value in initial_list:
    word_list = value.split()
    tagged = pos_tag(word_list)
    list_of_words_to_change = set()
    for val1, val2 in tagged:
        if val2 not in pos_to_exclude:
            list_of_words_to_change.add((val1, pos_converter.get(val2)))
    modified_pos_list.append((value, list_of_words_to_change))

print(f"List of allowed words that we need to work on : {initial_list}")

get_new_pos_tagged(modified_pos_list)

with open('original.txt', 'w') as f:
    for item in initial_list:
        f.write("%s\n" % item)
with open('modified.txt', 'w') as f:
    for item in modified_sentences:
        f.write("%s\n" % item)

print(f"Synonym List for CEFR Level C having only B's : {syn_dict_c}")
print(f"Synonym List for CEFR Level B having only A's : {syn_dict_b}")
