import copy
import json
import os
import queue
import re
import time

import pymupdf as fitz
from nltk import pos_tag
from nltk.corpus import stopwords

from config import Config
from intelli_e_reader.reader.cefr import Cefr
from intelli_e_reader.reader.syn_retriever import SynRetriever
from intelli_e_reader.reader.semantic_check import SemanticCheck

cefr_level = Cefr()
synonym_class = SynRetriever()
semantic_class = SemanticCheck()


class Word(object):
    def __init__(self, score, synonym_word, synonym_cefr, sentence, original_word):
        self.score = score
        self.synonym_word = synonym_word
        self.sentence = sentence
        self.original_word = original_word
        self.synonym_cefr = synonym_cefr

    def __lt__(self, other):
        return self.score > other.score

    def __gt__(self, other):
        return self.score < other.score


class CustomReader:
    # TAG's to exclude as they are conjunctions or Pronouns or words like where,how,what etc
    pos_to_exclude = ['CC', 'CD', 'MD', 'NNP', 'NNPS', 'PDT', 'DT', 'PRP', 'PRP$', 'RP', 'TO', 'WDT', 'WP', 'WRB']

    # NLTK tag list -> custom tag for project
    pos_converter = {'NN': 'n', 'NNS': 'n', 'VB': 'v', 'VBG': 'v', 'VBD': 'v',
                      'VBN': 'v', 'VBP': 'v', 'VBZ': 'v', 'JJ': 'aj', 'JJR': 'aj', 'JJS': 'aj',
                      'RB': 'av', 'RBR': 'av', 'RBS': 'av', 'IN': 'pp', 'CC': 'cj'}

    # stop words - words that we don't want to include
    # 1. Subordinating Conjunction
    stop_words_subs = ['after', 'although', 'as if', 'as long as', 'as much as', 'as soon as', 'as though', 'because',
                        'before', 'by the time', 'even if', 'even though', 'if', 'if only', 'if then', 'if when',
                        'in as much',
                        'in order that', 'lest', 'now', 'now since', 'now that', 'now when', 'once', 'provided',
                        'provided that',
                        'rater than', 'since', 'so that', 'supposing', 'than', 'that', 'though', 'til', 'unless',
                        'until',
                        'when', 'where', 'whereas', 'whenever', 'wherever', 'where if', 'which', 'while', 'who',
                        'whoever', 'why']

    # 2. Co-ordinating Conjunction
    stop_words_conj = ['For', 'Nor', 'But', 'Or', 'Yet', 'So', "you're", "They're", "monthly", "month",
                        "yearly", "year", "daily", "day"]

    '''
    Dictionary Structure : {word:([A_CEFR_LIST],[B_CEFR_LIST],[C_CEFR_LIST])}
    '''
    synonym_dict = {}

    '''
    Used as a class variable to initialise the initial highest
    score @ Level 0 - {When sentences are scored during the first semantic check run}
    '''
    initial_highest_score = 0.00

    '''
    Number of levels the sentences can recurse through
    in order to find a perfect synonym of the lowest CEFR order
    '''
    max_allowed_levels = 5

    '''
    List to maintain words Track as they recurse through
    multiple levels
    '''
    word_tracker = []

    def __init__(self, page_number=0, file_path_to_pdf=""):
        self.pdf_document = file_path_to_pdf
        # Open the PDF Document as doc
        self.doc = fitz.open(self.pdf_document)
        # Load Page based on Page number
        self.page = self.doc.load_page(page_number)
        # Split the page as paragraphs
        self.page_block = self.page.get_text("blocks")
        # Add conjunctions to the list of stop words - Note: Some conjunction
        # which are not in stopwords('english') are added here
        list_of_stop_words = list(self.stop_words_conj)
        # Extend the list of NLTK stop words
        list_of_stop_words.extend(stopwords.words("english"))
        self.stop_words = set(list_of_stop_words)
        self.title = self.doc.metadata.get('title')
        self.author = self.doc.metadata.get('author')

        # Per-instance state (was global/class-level in the original prototype)
        self.synonym_dict = {}
        self.set_a = queue.PriorityQueue()
        self.set_b = queue.PriorityQueue()
        self.set_c = queue.PriorityQueue()
        self.word_tracker = []
        self.grammer_checked_list = set()

    def iterate_over_paragraph(self, to_reduce=False, to_increase=False):
        '''
        Use this method once the page has been loaded
        1. Work on each paragraph
        2. Split paragraph as sentences
        3. Prepare the Synonyms list of all the eligible words
        4. Decrease or Increase the CEFR level of a word - In each sentence
        5. Grammar pass (see grammer_check)
        6. Return a json response
        '''
        if len(self.page_block) != 0:
            # List of (sentence,[word_to_replace,pos_tag])
            master_data = []
            # Position to indicate where each paragraph breaks
            # Contains (paragraph_no,line_no,number of words in the same)
            para_break = []

            for index, value in enumerate(self.page_block):
                # Start with the paragraph
                paragraph_to_operate = value[4]
                # Break the paragraph into lines
                initial_list = paragraph_to_operate.split('.')
                list_without_breaks = []

                for line_no, sentence in enumerate(initial_list):
                    # To identify true 'period'
                    position_of_break = -1

                    flag = sentence.endswith('\n')
                    if flag and (sentence != ' ' or sentence != ''):
                        position_of_break = sentence.index("\n")

                    new_sentence = sentence.strip().replace("-\n", '').replace('\n', ' ').replace('\t', ' ')
                    if new_sentence != ' ' or new_sentence != '':
                        if line_no == 0 and flag:
                            is_line_special = True
                        else:
                            is_line_special = False
                        para_break.append((index, line_no, len(new_sentence), is_line_special, position_of_break))

                        list_without_breaks.append((new_sentence, not flag))

                '''
                Each sentence present in the list must be iterated and reduced
                '''
                for sentence, period_flag in list_without_breaks:
                    # Break the list into word Tokens
                    list_data = sentence.split()

                    # Contains words which have no special characters & converted to lower
                    clean_list = []

                    # Clean the word by removing unwanted special characters
                    for word in list_data:
                        t = re.sub('[.?;,"]', "", word.lower())
                        # Remove all the unwanted standard stop words and user defined stop words
                        if t not in self.stop_words and word not in [',', '.', '?', '_', ';', '"', "'", ';', ':']:
                            clean_list.append(t)

                    if len(clean_list) > 0:
                        # Tag the words with their part of speech
                        pos_tag_tuple = pos_tag(clean_list)
                        refined_pos_tag_tuple = self.filter_pos(pos_tag_tuple)
                        if (refined_pos_tag_tuple is not None) and (len(refined_pos_tag_tuple) != 0):
                            # Each sentence will get a set of words eligible to be changed
                            master_data.append((sentence, refined_pos_tag_tuple, period_flag))
                    else:
                        if sentence != " " or sentence != "":
                            master_data.append((sentence, None, period_flag))

            # For each eligible word, derive the synonyms
            for _, tuple_data, _ in master_data:
                if tuple_data is not None:
                    self.generate_synonyms(tuple_data)

            refined_sentence_list = []

            # Indicating the line number
            number = 0

            '''
            Iterate over each sentence and reduce to lower or higer CEFR Level
            '''
            dict_with_sentence_data = {}

            list_to_save_tracker_words = []
            period_flag = True

            for sentence, tuple_data, period_flag in master_data:
                if to_reduce:
                    '''
                    When CEFR has to be lowered, reach  this
                    '''
                    if period_flag is False:
                        '''
                        Indicates a false period, store data until real
                        '''
                        list_to_save_tracker_words.append((sentence, tuple_data))

                    else:
                        '''
                        Indicates a real period, utilise the stored data
                        '''
                        local_list = []
                        list_tuple = []
                        # retrieve Stored data if any
                        for stored_sentence, tuple_info in list_to_save_tracker_words:
                            local_list.append(stored_sentence)
                            if tuple_info is not None:
                                list_tuple.extend(tuple_info)

                        # Store incoming data
                        local_list.append(sentence)
                        if tuple_data is not None:
                            list_tuple.extend(tuple_data)

                        list_to_save_tracker_words = []
                        refined_sentence, trace = self.refine_sentence_to_lower(" ".join(local_list), list_tuple)
                        refined_sentence_list.append(refined_sentence)

                    if period_flag:
                        dict_with_sentence_data[f"sentence_{number}"] = trace
                        number += 1

                elif to_increase:
                    '''
                    When CEFR has to be improved, reach  this
                    '''
                    refined_sentence = self.refine_sentence_to_upper(sentence, tuple_data)
                    refined_sentence_list.append(refined_sentence)

            # If the sentence were stored and not recovered because we never
            # encountered another True period sentence
            local_list = []
            list_tuple = []
            if len(list_to_save_tracker_words) > 0:
                for stored_sentence, tuple_info in list_to_save_tracker_words:
                    local_list.append(stored_sentence)
                    if tuple_info is not None:
                        list_tuple.extend(tuple_info)

                refined_sentence, trace = self.refine_sentence_to_lower(" ".join(local_list), list_tuple)
                refined_sentence_list.append(refined_sentence)

            '''
            Grammar pass over the simplified sentences.
            '''
            self.grammer_checked_list = set()
            self.grammer_check(refined_sentence_list)

            '''
            Since operation is performed by thread, sentence order is scatterd,
            sort the sentences based on their positional index
            '''
            sorted_grammer_checked_sentences = sorted(self.grammer_checked_list, key=lambda x: x[1])

            list_to_hold_sorted_data = []

            for sentence, _ in sorted_grammer_checked_sentences:
                list_to_hold_sorted_data.append(sentence)

            # Variable which contains all the complete page info after Reduction/Increase & Grammer Check
            reduced_checked_page_data = "".join(list_to_hold_sorted_data).strip().replace(".", '')

            altered_token_list = reduced_checked_page_data

            para_dictionary = {}

            '''
            To understand the number of sentences in the
            paragraph, we use the below
            '''
            for para_number, _, character_width, is_line_special, break_index in para_break:
                '''
                If Character width is 0, then it means it was previously
                a \n or \t
                '''
                if para_dictionary.get(para_number) is None:
                    para_dictionary[para_number] = 1
                elif character_width > 0:
                    value = para_dictionary.get(para_number)
                    para_dictionary[para_number] = 1 + value

            '''
            String for json response
            '''
            marked_string = []

            '''
            Re pack sentences for pdf, based on the
            pre-determined sentence count in a
            paragraph
            '''
            for index, value in para_dictionary.items():
                content = list_to_hold_sorted_data[:value]
                self.re_pack_sentence(index, content)
                # Mark \n and \t for the final json response
                marked_string.append(f"{''.join(content)}\n \t ")
                # Remove the unused data from list
                list_to_hold_sorted_data = list_to_hold_sorted_data[value:]
            return {"title": self.title, "author": self.author, "sentence_list": dict_with_sentence_data,
                    "formatted_text": "".join(marked_string)}
        else:
            return None

    def grammer_check(self, refined_sentence_list):
        '''
        Grammar-correction pass over each simplified sentence.

        The original prototype called the Ginger web API (via the `gingerit`
        package) here, using 3 threads to correct each sentence in parallel.
        That service is no longer available (the `gingerit` package on PyPI
        is an unrelated placeholder, and the underlying Ginger API is
        unreachable), so this is a passthrough: sentences are used as-is,
        with the ordering/index bookkeeping the rest of the pipeline expects
        preserved.
        '''
        self.grammer_checked_list = set(
            (sentence.strip() + ".", index) for index, sentence in enumerate(refined_sentence_list)
        )

    def filter_pos(self, pos_tag_tuple=None):
        '''
        This function filter's out the pos_tag we would require to check
        '''
        if pos_tag_tuple is not None and (len(pos_tag_tuple) != 0):
            modified_tuple_list = []
            for word, pos in pos_tag_tuple:
                if pos not in self.pos_to_exclude:
                    m_pos = self.pos_converter.get(pos)
                    if m_pos is not None and (str(word).startswith("'") is False):
                        modified_tuple_list.append((word.replace('[,.?;]', ""), m_pos))
            return modified_tuple_list

    def re_pack_sentence(self, index_to_change, list_data):
        '''
        This function is utilised once the
        1. Sentence is reduced/increased
        2. Grammer checked
        3. Ready for adding text to new PDF
        '''
        string_mod = " ".join(list_data)
        to_change = list(self.page_block[index_to_change])
        to_change[4] = string_mod
        self.page_block[index_to_change] = tuple(to_change)

    def create_new_pdf(self, name_of_file="modified_data"):
        '''
        Use this function to write a pdf,
        1. Always ensure self.page_blocks is populated before hand
        We Call this after self.repack in iterate_through_paragraph()
        '''
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        font_file = Config.ASSETS_FOLDER + "/fonts/urw-palladio-l-roman.ttf"

        new_doc = fitz.open()
        page = new_doc.new_page()
        for value in self.page_block:
            rectangle = fitz.Rect(value[0], value[1], value[2], value[3])
            wr = fitz.TextWriter(page.rect)
            rect = fitz.Rect(rectangle)
            fon = fitz.Font(fontname='URWPalladioL', fontfile=font_file)
            wr.fill_textbox(rect=rect, text=value[4], fontsize=13.9, align=fitz.TEXT_ALIGN_JUSTIFY, font=fon,
                             lineheight=1.21)
            rect.y0 = wr.last_point.y
            wr.write_text(page)

        base_name = os.path.splitext(os.path.basename(name_of_file))[0]
        out_path = os.path.join(Config.OUTPUT_FOLDER, base_name + "_reduced.pdf")
        new_doc.save(out_path)
        return out_path

    def generate_synonyms(self, refined_pos_tag_tuple):
        '''
        This method generates synonyms for the requested word list
        Value is populated in the instance dict for synonyms and can be accessed from there
        Not Thread SAFE
        '''
        for word_to_check, part_of_speech in refined_pos_tag_tuple:
            cefr_level_word = cefr_level.getCefr(word_to_check, part_of_speech)
            if cefr_level_word is not None and cefr_level_word != 'A':
                # Check if the synonym list is not already present
                if word_to_check not in self.synonym_dict:
                    # Get the synonyms list
                    synonym_list = synonym_class.retrieveSynsByPos(word_to_check, part_of_speech)
                    if len(synonym_list) != 0:
                        # Split the synonyms list as A,B and C cefr level lists
                        list_a, list_b, list_c = self.get_seperated_synonyms(synonym_list, part_of_speech)
                        # Store that list as a tuple with (A_CEFR_LIST,B_CEFR_LIST,C_CEFR_LIST)
                        self.synonym_dict[word_to_check] = (list_a, list_b, list_c)

    def get_seperated_synonyms(self, synonym_list, part_of_speech):
        '''
        This ensures the list of synonyms is seperated as
        list for cefr A, list for cefr B and list for cefr C
        '''
        list_for_a = []
        list_for_b = []
        list_for_c = []
        for word in synonym_list:
            refined_word = re.sub('[.?;,"]', "", word.lower())
            lv = cefr_level.getCefr(refined_word, part_of_speech)
            if lv is not None:
                if lv == 'A':
                    list_for_a.append(refined_word)
                elif lv == 'B':
                    list_for_b.append(refined_word)
                else:
                    list_for_c.append(refined_word)
        return list_for_a, list_for_b, list_for_c

    def refine_sentence_to_lower(self, sentence, tuple_data=None):
        '''
        Main method to ensure words in sentences are reduced to lowest possible
        level
        '''
        if tuple_data is None:
            tuple_data = {}

        new_sentence = copy.deepcopy(sentence)
        track_log = {}

        for word, part_of_speech in tuple_data:

            refined_main_word = re.sub('[.?;,"]', "", word.lower())
            main_word_cefr_level = cefr_level.getCefr(refined_main_word, part_of_speech)

            if (main_word_cefr_level is not None) and (word in self.synonym_dict):
                target_cefr = []
                # If Main word is B: Eligible ones are A or B
                if main_word_cefr_level == 'B':
                    target_cefr.append('A')
                else:
                    # If Main word Cefr is C, eligible ones are A,B,C
                    target_cefr.append('A')
                    target_cefr.append('B')

                # Get Synonyms
                synonym_list = self.synonym_dict.get(word)

                # Get index for the requested word
                index = str(re.sub('[.?;,"]', "", new_sentence.lower())).split().index(word)

                # To create a list of word_iteration chart, use this tracker
                tracker_key = f"index_{index}"

                # Clear the tracker at each instance
                # Contains set of all words for a sentence
                self.word_tracker = list()

                # Adds original word data to the first position in "childrens" key
                self.word_tracker.append({"word": word, "cefr": main_word_cefr_level, "sentence": new_sentence})

                # Request to get the highest score from
                # Set of A,B and C Cefr that is generated for each word
                word_object = self.get_highest_score_word_tuple(new_sentence, word, synonym_list, index,
                                                                  part_of_speech)

                # Contains the final selected word before return
                qualified_word = {}

                if word_object is not None:

                    if word_object.synonym_cefr in target_cefr:
                        '''
                        Found eligible word, return
                        '''
                        qualified_word = self.create_dict(word_object)
                        new_sentence = word_object.sentence
                    else:
                        # Need to parse down  levels to figure out a lower level cefr word
                        self.initial_highest_score = word_object.score

                        # To ensure, already checked word is not checked again
                        self.word_tracker.append(self.create_dict(word_object))
                        newlist = [word_object.synonym_word]

                        # Recurse though lower levels
                        word_instance = self.level_down(word_object, part_of_speech, target_cefr, 1, newlist)

                        if word_instance.synonym_cefr >= main_word_cefr_level:
                            '''
                            Received a higher or equal to word
                            try to fetch the lowest CEFR word generated by recursion
                            '''
                            word_instance = self.get_a_sentence(word_instance, main_word_cefr_level)

                            if word_instance.synonym_cefr > main_word_cefr_level:
                                # Received a higher instance word, so use the main word itself
                                if word_instance.synonym_word not in newlist:
                                    self.word_tracker.append(self.create_dict(word_instance))
                                new_sentence = sentence
                                qualified_word = {"word": word, "cefr": main_word_cefr_level,
                                                   "sentence": new_sentence}
                            else:
                                # Use the received word
                                qualified_word = self.create_dict(word_instance)
                                new_sentence = word_instance.sentence

                        else:
                            qualified_word = self.create_dict(word_instance)
                            new_sentence = word_instance.sentence

                    # Clear the Priority queue for next word from
                    # the main sentence
                    self.set_a = queue.PriorityQueue()
                    self.set_b = queue.PriorityQueue()
                    self.set_c = queue.PriorityQueue()

                    if len(self.word_tracker) > 0:
                        qualified_word["children"] = self.word_tracker
                    track_log[tracker_key] = qualified_word

        return new_sentence, track_log

    def create_dict(self, word_object):
        '''
        {
          "word":
          "score"
          "cefr":
          "sentence":
        }
        '''
        qualifier = {}
        qualifier["word"] = word_object.synonym_word
        qualifier["score"] = word_object.score
        qualifier["cefr"] = word_object.synonym_cefr
        qualifier["sentence"] = word_object.sentence
        return qualifier

    def get_a_sentence(self, obj, cefr_level_target):
        '''
        Check the lower cefr sets to find the lowest cefr level word
        if C - > get set B or set A
        if B - > get lowest of set A
        '''
        score_1 = 0.00
        score_2 = 0.00
        word_a = None

        if cefr_level_target == 'C':
            if len(self.set_a.queue) != 0:
                word_a = self.set_a.queue[0]
                score_1 = word_a.score
            if len(self.set_b.queue) != 0:
                word_b = self.set_b.queue[0]
                score_2 = word_b.score
            if (score_1 == score_2) and score_1 == 0.00:
                return obj
            elif score_1 == score_2:
                return word_a
            elif score_1 > score_2:
                return word_a
            else:
                return word_b
        else:
            if len(self.set_a.queue) != 0:
                word_a = self.set_a.queue[0]
                score_1 = word_a.score
            if score_1 == 0.00:
                return obj
            else:
                return word_a

    def level_down(self, word_obj, pos, target_cefr, level, list_of_existing_words):
        if (level == self.max_allowed_levels) or ((word_obj.score == self.initial_highest_score) and level > 1):
            return word_obj
        else:
            word = word_obj.synonym_word
            self.generate_synonyms([(word, pos)])
            syn_list = self.synonym_dict.get(word)

            if syn_list is None or (len(syn_list) == 0):
                return word_obj
            else:
                index = str(re.sub('[.?;,"]', "", word_obj.sentence.lower())).split().index(word)
                word_object = self.get_highest_score_word_tuple(word_obj.sentence, word, syn_list, index, pos)

                if word_object is not None:
                    if word_object.synonym_cefr in target_cefr:
                        return word_object

                    else:
                        if word_object.synonym_word not in list_of_existing_words:
                            self.word_tracker.append(self.create_dict(word_object))
                            list_of_existing_words.append(word_object.synonym_word)
                            return self.level_down(word_object, pos, target_cefr, level + 1, list_of_existing_words)
                        else:
                            return word_obj
                else:
                    return word_obj

    def refine_sentence_to_upper(self, sentence, tuple_data):
        # Not implemented in the original prototype either -- CEFR level was
        # only ever reduced, never increased.
        return sentence

    def get_top_one(self, new_sentence, word, list_data, index, part_of_speech):
        '''
        Checks the synmantic scores of the synonym words
        Returns the highest from CEFR_A,B and C
        '''
        acceptable_synonyms_list = semantic_class.checkSynPos(new_sentence, word, list_data, index,
                                                                part_of_speech)

        if len(acceptable_synonyms_list) != 0:
            return semantic_class.calcSemanticScore(new_sentence, word, acceptable_synonyms_list, index,
                                                      part_of_speech)
        else:
            return None

    def get_highest_score_word_tuple(self, new_sentence, word, synonym_list, index, part_of_speech):
        '''
        Performs the Priority Queue function
        Orders the highest score element to first as and when data is queued

        Return the top scoring value out of Cefr_set A,B and C
        '''
        queu = queue.PriorityQueue()
        value_a = self.get_top_one(new_sentence, word, synonym_list[0], index, part_of_speech)
        value_b = self.get_top_one(new_sentence, word, synonym_list[1], index, part_of_speech)
        value_c = self.get_top_one(new_sentence, word, synonym_list[2], index, part_of_speech)

        if value_a is not None:
            word_new = Word(value_a[0], value_a[1], 'A', value_a[2], word)
            queu.put(word_new)
            self.set_a.put(word_new)
        if value_b is not None:
            word_new = Word(value_b[0], value_b[1], 'B', value_b[2], word)
            queu.put(word_new)
            self.set_b.put(word_new)
        if value_c is not None:
            word_new = Word(value_c[0], value_c[1], 'C', value_c[2], word)
            queu.put(word_new)
            self.set_c.put(word_new)

        if len(queu.queue) != 0:
            return queu.queue[0]


class ConvertPdf:

    def __init__(self, low_score=97.00, required_level='A'):
        '''
        Alter this value for a score that is considered as low
        '''
        self.low_score = low_score
        self.required_level = required_level
        self.json_string = {}

    def convert(self, file_path=None, page_number=0, write_pdf=True):
        if file_path is None:
            raise ValueError("file_path is required")

        start_time = time.time()

        # This will unpack the PDF and initialise the required variables
        custom = CustomReader(file_path_to_pdf=file_path, page_number=page_number)
        # Perform the reduction on the unpacked data
        json_data = custom.iterate_over_paragraph(to_reduce=True)

        if json_data is not None:
            if write_pdf:
                custom.create_new_pdf(file_path)
            self.json_string = json_data

        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        with open(os.path.join(Config.OUTPUT_FOLDER, 'json_data.json'), 'w') as fout:
            json.dump(self.json_string, fout)

        print(f"Time taken to Perform task {time.time() - start_time} (secs)")
        return self.json_string
