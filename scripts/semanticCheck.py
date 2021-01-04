import scipy
import copy
from sentence_transformers import SentenceTransformer
from nltk.tag import pos_tag

class SemanticCheck:
    # NLTK tag list -> custom tag for project
    pos_convert = {'NN': 'n', 'NNS': 'n', 'VB': 'v', 'VBG': 'v', 'VBD': 'v',
                   'VBN': 'v', 'VBP': 'v', 'VBZ': 'v', 'JJ': 'aj', 'JJR': 'aj', 'JJS': 'aj',
                   'RB': 'av', 'RBR': 'av', 'RBS': 'av', 'IN': 'pp', 'CC': 'cj'}

    def __init__(self):
        self.model = SentenceTransformer('bert-base-nli-mean-tokens')

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
        words = query.split(' ')
        sentences = list()

        for synonym in synonyms:
            word_list = copy.deepcopy(words)
            word_list[index] = synonym
            sentence = ''
            for word in word_list:
                sentence = sentence + ' ' + word
            sentences.append(sentence.strip())

        # separator = '\n'
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
        # count = 0
        for tag in tagged_sent:
            # TODO : Please check if this is OK!
            # if tag[0] == word and index == count:
            #     req_pos = tag[1]
            #     count += 1
            #     continue
            if tag[0] in synonyms and self.pos_convert.get(tag[1]) == req_pos:
                acceptable_syns.add(tag[0])
            # count += 1
        return acceptable_syns

    def calcSemanticScore(self, query, word, synonyms, index):
        """Calculates the semantic similarity for the sentences with syns substituted.

        Args:
            query (string): The original sentence
            word (string): Word to be replaced
            synonyms ([string]): List of synonyms of the word to be replaced.
            index (int): Position of the word in the query

        Returns:
            [tuple]: Returns a list of tuples of (word, similarity, sentence)
        """

        merged_sentences, sentences = self.form_sentences(query, word, synonyms, index, '\n')
        corpus = [i for i in merged_sentences.split('\n') if i != '' and len(i.split(' ')) >= 4]
        corpus_embeddings = self.model.encode(corpus)

        queries = [query]
        query_embeddings = self.model.encode(queries)

        closest_n = 5

        # Compute distances for the sentences.
        for query, query_embedding in zip(queries, query_embeddings):
            distances = scipy.spatial.distance.cdist([query_embedding], corpus_embeddings, "cosine")[0]

            syn_distances = zip(synonyms, 1 - distances, sentences)
            syn_distances = sorted(syn_distances, key=lambda x: x[1], reverse=True)

        return syn_distances[:closest_n]
