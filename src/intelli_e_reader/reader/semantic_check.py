import copy
import os

from sentence_transformers import SentenceTransformer, util
from nltk.tag import pos_tag


class SemanticCheck:
    # NLTK tag list -> custom tag for project
    pos_convert = {'NN': 'n', 'NNS': 'n', 'VB': 'v', 'VBG': 'v', 'VBD': 'v',
                   'VBN': 'v', 'VBP': 'v', 'VBZ': 'v', 'JJ': 'aj', 'JJR': 'aj', 'JJS': 'aj',
                   'RB': 'av', 'RBR': 'av', 'RBS': 'av', 'IN': 'pp', 'CC': 'cj'}

    def __init__(self, device=None):
        # Default to CPU: torch.cuda.is_available() can return True even when
        # the installed torch build has no kernels for the local GPU (e.g. a
        # GPU newer than the build supports), which fails at inference time
        # rather than at this check. Opt into GPU explicitly via the
        # INTELLI_DEVICE env var (or the constructor arg) once you've
        # confirmed `torch.cuda.is_available()` AND a real encode() call both
        # work on your machine.
        if device is None:
            device = os.environ.get('INTELLI_DEVICE', 'cpu')
        self.model = SentenceTransformer('roberta-base-nli-stsb-mean-tokens', device=device)

    def form_sentences(self, query, word, synonyms, index, seperator):
        """This method makes sentences for all the synonyms of the word provided.

        Args:
            query (string): The original sentence
            word (string): Word to be replaced
            synonyms ([string]): List of synonyms of the word to be replaced.
            index (int): Position of the word in the query
            seperator (string): Seperator for the combined sentences

        Returns:
            (string, [string]): A string of the merged sentences, list of individual sentences
        """
        words = query.replace("\n", " ").split(' ')
        sentences = list()

        for synonym in synonyms:
            word_list = copy.deepcopy(words)
            word_list[index] = synonym
            sentence = ''
            for word in word_list:
                sentence = sentence + ' ' + word
            sentences.append(sentence.strip())

        merged_sentences = seperator.join(sentences)
        return merged_sentences, sentences

    def checkSynPos(self, query, word, synonyms, index, req_pos):
        """Returns syns with same PoS as the original word.

        Args:
            query (string): The original sentence.
            word (string): Word to be replaced.
            synonyms ([string]): List of synonyms of the word to be replaced.
            index (int): Position of the word in the query.
            :param req_pos: part of speech we are looking for

        Returns:
            [string]: List of acceptable synonyms.
        """
        wordList = copy.deepcopy(synonyms)
        wordList.insert(0, word)
        merged_sentences, sentences = self.form_sentences(query, word, wordList, index, '\n')
        del sentences
        tagged_sent = pos_tag(merged_sentences.split())

        acceptable_syns = set()

        for tag in tagged_sent:
            if tag[0] in synonyms and self.pos_convert.get(tag[1]) == req_pos:
                acceptable_syns.add(tag[0])

        return acceptable_syns

    def calcSemanticScore(self, query, word, synonyms, index, part_of_speech=None):
        """Calculates the semantic similarity for the sentences with syns substituted.

        Args:
            query (string): The original sentence
            word (string): Word to be replaced
            synonyms ([string]): List of synonyms of the word to be replaced.
            index (int): Position of the word in the query
            part_of_speech: unused, kept for call-signature compatibility

        Returns:
            [tuple]: Returns a list of tuples of (score, word, sentence), highest score first.
        """
        corpus = []

        for val in synonyms:
            words = query.split()
            words[index] = val
            corpus.append(" ".join(words))

        if len(corpus) == 1:
            corpus.append(query)

        paraphrases = util.paraphrase_mining(self.model, corpus, corpus_chunk_size=len(corpus), top_k=1)

        result_list = set()

        for scores, i, j in paraphrases:
            result_list.add((scores, corpus[i].split()[index], corpus[i]))

        sorted_list = sorted(result_list, key=lambda x: x[0], reverse=True)

        return sorted_list[0]
