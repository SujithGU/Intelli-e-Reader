import pickle
import re

import nltk
import numpy as np
import pandas as pd
import tensorflow as tf
from numpy import argmax
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical

from config import Config
from intelli_e_reader.cefr_model import train
from intelli_e_reader.data_pipeline.google_ngram_parser import get_ngram_data_all
import time


class Predictor:

    def __init__(self):
        nltk.download('averaged_perceptron_tagger')

        self.ngram_tag_dictionary = {'CC': 'CONJ', 'IN': 'CONJ', 'CD': '',
                                     'DT': 'DET', 'JJ': 'ADJ', 'JJR': 'ADJ',
                                     'JJS': 'ADJ', 'MD': '', 'NN': 'NOUN', 'NNS': 'NOUN',
                                     'NNP': 'NOUN', 'NNPS': 'NOUN', 'PRP': 'PRON', 'PRP$': 'PRON',
                                     'RB': 'ADV', 'RBR': 'ADV', 'RBS': 'ADV', 'TO': '',
                                     'VB': 'VERB', 'VBD': 'VERB', 'VBG': 'VERB', 'VBN': 'VERB', 'VBZ': 'VERB',
                                     'VBP': 'VERB', 'WDT': '', 'WP': '', 'WP$': '', 'WRB': '', 'EXC': ''}

        # Read the all all_english_words_tagged_file for encoding purpose - Contains 370,100 words
        df = pd.read_csv(f'{Config.PROCESSED_DATA_FOLDER}/all_english_words_tagged.csv')

        # Encode words
        self.word_list = np.array(df['eng_words'])

        label_encoder = LabelEncoder()

        self.integer_encoding = label_encoder.fit_transform(self.word_list)
        integer_coded = self.integer_encoding.reshape(len(self.integer_encoding), 1)
        # One hot encode with Keras backend
        keras_encode_array = to_categorical(self.integer_encoding)

        print(f'Integer Encoded - {self.integer_encoding}')
        print(f'One Hot Encoded  - {keras_encode_array}')
        print(f'Checking One hot Encode - {label_encoder.inverse_transform([argmax(keras_encode_array[0, :])])}')
        print(f'Checking Integer Encode - {label_encoder.inverse_transform(integer_coded[0, :])}')

        # Encode PoS
        pos_unique_list = df['pos_tag'].unique()
        # Additions apart from the standards
        pos_unique_list = np.append(pos_unique_list, 'ADP')
        pos_unique_list = np.append(pos_unique_list, 'EXC')
        pos_unique_list = np.append(pos_unique_list, '')
        pos_unique_list = np.append(pos_unique_list, 'MVB')
        pos_unique_list = np.append(pos_unique_list, 'AVB')
        pos_unique_list = np.append(pos_unique_list, 'PRONOUN')
        pos_unique_list = np.append(pos_unique_list, 'PHR')
        pos_unique_list = np.append(pos_unique_list, 'PRON')

        self.label_encoder_pos = LabelEncoder()

        self.integer_encoding_pos = self.label_encoder_pos.fit_transform(pos_unique_list)
        integer_coded_pos = self.integer_encoding_pos.reshape(len(self.integer_encoding_pos), 1)
        # One hot encode with Keras backend
        keras_encode_pos = to_categorical(integer_coded_pos).astype('float32')

        print(f'Integer Encoded - {self.integer_encoding_pos}')
        print(f'One Hot Encoded  - {keras_encode_pos}')
        print(f'Checking One hot Encode - {self.label_encoder_pos.inverse_transform([argmax(keras_encode_pos[0, :])])}')
        print(f'Checking Integer Encode - {self.label_encoder_pos.inverse_transform(integer_coded_pos[0, :])}')

        self.sub_optimal_classifier = pickle.load(
            open(f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_models/sub_optimal_classifier2.pkl', 'rb'))

        self.nn_model = tf.keras.models.load_model(
            f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_models/sub_optimal_nn_model2.h5')

        self.optimal_classifier = pickle.load(
            open(f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_models/optimal_classifier_final.pkl', 'rb'))

    def predict(self, word=None, pos=None):
        word = word
        pos = pos

        # Clean the word
        word = re.sub(r'[?|$|.|!]', r'', word)
        word = word.lower()

        # Set the PoS
        if pos is None or pos == '':
            n_pos = nltk.pos_tag([word])[0][1]
            pos = self.ngram_tag_dictionary[n_pos]

        list_all = get_ngram_data_all(word=word, pos=pos)
        # 1
        ngram_2013 = round(list_all[0],6)
        # 2
        ngram_2014 = round(list_all[1],6)
        # 3
        ngram_2015 = round(list_all[2],6)
        # 4
        ngram_2016 = round(list_all[3],6)
        # 5
        ngram_2017 = round(list_all[4],6)
        # 6
        ngram_2018 = round(list_all[5],6)
        # 7
        ngram_2019 = round(list_all[5],6)
        # 8
        word_count = train.count_words(word)
        # 9
        letter_count = train.count_letters(word)
        # 10
        syllable_count = train.syllable_count(word)

        # 11
        index = list(self.word_list).index(word)
        one_hot_word = self.integer_encoding[index]

        # 12
        pos_encoded_dict = {}
        for value in self.integer_encoding_pos:
            key = self.label_encoder_pos.inverse_transform([value])
            pos_encoded_dict[key[0]] = value

        one_hot_pos = pos_encoded_dict[pos]

        X = np.array([[ngram_2013, ngram_2014, ngram_2015, ngram_2016,
                       ngram_2017, ngram_2018, ngram_2019, letter_count,
                       syllable_count, word_count, one_hot_word, one_hot_pos]])

        Y_RF = self.sub_optimal_classifier.predict(X)

        Y_NN = self.nn_model.predict(X)

        rf_pred = Y_RF[0]
        nn_pred = np.argmax(Y_NN[0])

        X = np.append(X, [rf_pred, nn_pred])
        X = X.reshape(1, X.shape[0])

        Y_RF_F = self.optimal_classifier.predict(X)

        # nn_model_f = tf.keras.models.load_model(
        #     f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_models/optimal_nn_model_final.h5')
        #
        # Y_NN_F = nn_model_f.predict(X)

        rf_pred_f = Y_RF_F[0]
        # nn_pred_f = np.argmax(Y_NN_F[0])

        # print(f'Final NN Pred {nn_pred_f}')

        # final_cefr = math.ceil((rf_pred_f + nn_pred_f) / 2)
        return rf_pred_f


if __name__ == '__main__':
    predictor = Predictor()

    start = time.time()
    val = predictor.predict('triumvirate', 'NOUN')
    end = time.time()
    print(f'Final CEFR {val} {int(end - start)} secs')
