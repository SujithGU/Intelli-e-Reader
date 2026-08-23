import math
import pickle
import re

import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import tensorflow as tf
from keras.layers import Dense, Dropout
from numpy import argmax
from sklearn import metrics
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical

from config import Config


# from sklearn.preprocessing import StandardScaler


# Count Number of letter
def count_letters(w=None):
    return round(len(w), 6)


# Count words which are compounded with a '-'
def count_words(w=None):
    return round(len(w.split('-')), 6)


def syllable_count(w):
    w = w.lower()
    count = 0
    vowels = "aeiouy"
    if w[0] in vowels:
        count += 1
    for i in range(1, len(w)):
        if w[i] in vowels and w[i - 1] not in vowels:
            count += 1
    if w.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return round(count, 6)


def create_nn_model(shape=None):
    model = Sequential()

    model.add(Dense(20, input_shape=[shape], activation='relu', kernel_initializer='he_normal'))
    model.add(Dense(10, activation='relu', kernel_initializer='he_normal'))

    model.add(Dropout(0.04))
    model.add(Dense(7, activation='softmax'))

    return model


def train_on_random_forest(train_x, test_x, train_y, test_y, estimator=500):
    random_forest_classifier = RandomForestClassifier(n_estimators=estimator)
    random_forest_classifier.fit(train_x, train_y)

    y_pred = random_forest_classifier.predict(test_x)

    print("Accuracy:", metrics.accuracy_score(test_y, y_pred))
    return random_forest_classifier


def train_on_nn_network(train_x, test_x, train_y, test_y, model_name="dummy"):
    call_backs = [tf.keras.callbacks.ModelCheckpoint(f'{Config.MODELS_FOLDER}/cefr_prediction/{model_name}_weights.h5',
                                                     save_weights_only=True,
                                                     save_best_only=True,
                                                     mode='auto',
                                                     monitor='val_loss'),
                  tf.keras.callbacks.ReduceLROnPlateau(monitor='loss', factor=0.2,
                                                       patience=5, min_lr=0.00001),
                  tf.keras.callbacks.EarlyStopping(
                      monitor='loss', min_delta=0, patience=20, verbose=0,
                      mode='auto', baseline=None, restore_best_weights=False
                  )]

    ml_model = create_nn_model(train_x.shape[1])

    ml_model.compile(loss='sparse_categorical_crossentropy', optimizer=tf.keras.optimizers.Adam(learning_rate=0.00001),
                     metrics=['accuracy'])
    hist = ml_model.fit(train_x, train_y, epochs=1000, batch_size=32,
                        steps_per_epoch=math.ceil(len(train_x) / 32),
                        validation_steps=math.ceil(len(test_x) / 32),
                        validation_data=(test_x, test_y),
                        callbacks=call_backs
                        )
    ml_model.save(f'{Config.MODELS_FOLDER}/cefr_prediction/{model_name}.h5')
    return hist, ml_model


def train_on_svm(train_x, test_x, train_y, test_y, kernel='rbf'):
    print('Here')
    svm_classifier = svm.SVC(kernel=kernel, random_state=1, gamma=0.10, C=10.0)
    svm_classifier.fit(train_x, train_y)

    y_pred = svm_classifier.predict(test_x)

    print("Accuracy:", metrics.accuracy_score(test_y, y_pred))
    # print("Precision:", metrics.precision_score(test_y, y_pred))

    return svm_classifier


def plot_graph(histt=None):
    # plot graph

    plt.figure(figsize=(20, 5))
    plt.subplot(121)
    plt.plot(histt.history['accuracy'])
    plt.plot(histt.history['val_accuracy'])
    plt.title('Model Accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Test'], loc='upper left')

    # Plot training & validation loss values
    plt.subplot(122)
    plt.plot(histt.history['loss'])
    plt.plot(histt.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Test'], loc='upper left')

    plt.show()


if __name__ == '__main__':
    nltk.download('averaged_perceptron_tagger')

    ngram_tag_dictionary = {'CC': 'CONJ', 'IN': 'CONJ', 'CD': '',
                            'DT': 'DET', 'JJ': 'ADJ', 'JJR': 'ADJ',
                            'JJS': 'ADJ', 'MD': '', 'NN': 'NOUN', 'NNS': 'NOUN',
                            'NNP': 'NOUN', 'NNPS': 'NOUN', 'PRP': 'PRON', 'PRP$': 'PRON',
                            'RB': 'ADV', 'RBR': 'ADV', 'RBS': 'ADV', 'TO': '',
                            'VB': 'VERB', 'VBD': 'VERB', 'VBG': 'VERB', 'VBN': 'VERB', 'VBZ': 'VERB',
                            'VBP': 'VERB', 'WDT': '', 'WP': '', 'WP$': '', 'WRB': '', 'EXC': ''}

    # Read the all all_english_words_tagged_file for encoding purpose - Contains 370,100 words
    df = pd.read_csv(f'{Config.PROCESSED_DATA_FOLDER}/all_english_words_tagged.csv')

    # Encode words
    word_list = np.array(df['eng_words'])
    label_encoder = LabelEncoder()

    integer_encoding = label_encoder.fit_transform(word_list)
    integer_coded = integer_encoding.reshape(len(integer_encoding), 1)
    # One hot encode with Keras backend
    keras_encode_array = to_categorical(integer_encoding)

    print(f'Integer Encoded - {integer_encoding}')
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

    label_encoder_pos = LabelEncoder()

    integer_encoding_pos = label_encoder_pos.fit_transform(pos_unique_list)
    integer_coded_pos = integer_encoding_pos.reshape(len(integer_encoding_pos), 1)
    # One hot encode with Keras backend
    keras_encode_pos = to_categorical(integer_coded_pos).astype('float32')

    print(f'Integer Encoded - {integer_encoding_pos}')
    print(f'One Hot Encoded  - {keras_encode_pos}')
    print(f'Checking One hot Encode - {label_encoder_pos.inverse_transform([argmax(keras_encode_pos[0, :])])}')
    print(f'Checking Integer Encode - {label_encoder_pos.inverse_transform(integer_coded_pos[0, :])}')

    # Read the master_cefr with ngram's - Contains 7,620 words

    w_df = pd.read_csv(f'{Config.PROCESSED_DATA_FOLDER}/master_cefr_with_ngram.csv')

    for index, row in w_df.iterrows():
        word = row['word']
        word = re.sub(r'[?|$|.|!]', r'', word)
        w_df['word'][index] = word.lower()

    print(f'Shape of the Dataframe is : {w_df.shape}')

    # Check for pos = 'NAN' and change it to None
    for index, row in w_df.iterrows():
        if row['pos'] == 'NAN':
            w_df['pos'][index] = None

    # Count the number of NaN
    nan_count = w_df['pos'].isnull().sum()
    print(f'Count of words with no POS (Before Cleaning)- {nan_count}')

    # Tag words with no PoS
    for index, row in w_df.iterrows():
        if row['pos'] is None:
            nltk_pos = nltk.pos_tag([row['word']])[0][1]
            w_df['pos'][index] = ngram_tag_dictionary[nltk_pos]

    nan = w_df['pos'].isnull().sum()
    print(f'Count of words with no POS (After Cleaning) - {nan}')

    # Add more features
    word_count_list = []
    syllable_count_list = []
    letter_count_list = []

    word_list = w_df['word']

    for wrd in word_list:
        word_count_list.append(count_words(wrd))
        letter_count_list.append(count_letters(wrd))
        syllable_count_list.append(syllable_count(wrd))

    w_df['letter_count'] = word_count_list
    w_df['syllable_count'] = syllable_count_list
    w_df['complex_word_count'] = word_count_list

    # Drop un-wanted columns and change data type to float
    w_df = w_df.drop(columns=['cefr'])
    w_df.cefr_int = w_df.cefr_int.astype(float)
    w_df.letter_count = w_df.letter_count.astype(float)
    w_df.syllable_count = w_df.syllable_count.astype(float)
    w_df.complex_word_count = w_df.complex_word_count.astype(float)

    print(f'Data types of the cleaned data is \n{w_df.dtypes}')
    print(f'Shape of the new data set : {w_df.shape}')

    # Encode the words and the PoS
    word_list_encoding = []
    pos_list_encoding = []

    # Word encoding
    w_list = list(w_df['word'])

    for wrd in w_list:
        index = w_list.index(str(wrd))
        word_list_encoding.append(integer_encoding[index])

    # PoS Encoding
    pos_encoded_dict = {}

    for value in integer_encoding_pos:
        key = label_encoder_pos.inverse_transform([value])
        pos_encoded_dict[key[0]] = value

    for index, row in w_df.iterrows():
        value = row['pos']
        if value == '':
            pos_list_encoding.append(7)
        else:
            pos_list_encoding.append(pos_encoded_dict[value])

    # Add encoded values as features

    w_df['one_hot_word'] = word_list_encoding
    w_df['one_hot_pos'] = pos_list_encoding

    # Drop the words and pos character columns to make data set look clean

    copy_df = w_df

    w_df = w_df.drop(columns=['word', 'pos'])

    print(f'Final Shape of the cleaned and feature added data set is : {w_df.shape}')

    # Convert encoding from int to float
    w_df.one_hot_word = w_df.one_hot_word.astype(float)
    w_df.one_hot_pos = w_df.one_hot_pos.astype(float)

    # Dropping 645 row which has NaN values
    w_df = w_df.drop([645])

    # Prepare Train and Test Data Set
    dataset = w_df.values

    X = dataset[:, 1:]

    Y = dataset[:, 0]

    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=.20, random_state=42, stratify=Y)

    """
    Stage 1 Training
    """

    # Train on Random Forest
    classifier = train_on_random_forest(X_train, X_test, y_train, y_test, estimator=1000)
    pickle.dump(classifier, open(f'{Config.MODELS_FOLDER}/cefr_prediction/sub_optimal_classifier2.pkl', 'wb'))

    # Train on NN
    ht, mdl = train_on_nn_network(X_train, X_test, y_train, y_test, 'sub_optimal_nn_model2')
    plot_graph(ht)

    # No training on SVM

    # scaling = StandardScaler().fit(X_train)
    # X_train_norm = scaling.transform(X_train)
    # X_test_norm = scaling.transform(X_test)
    #
    # # Train on SVM
    # s_classifier = train_on_svm(X_train_norm, X_test_norm, y_train, y_test)

    # Generate features using base predictions
    sub_optimal_classifier = pickle.load(open(f'{Config.MODELS_FOLDER}/cefr_prediction/sub_optimal_classifier2.pkl', 'rb'))

    Y_RF = sub_optimal_classifier.predict(X)

    nn_model = tf.keras.models.load_model(f'{Config.MODELS_FOLDER}/cefr_prediction/sub_optimal_nn_model2.h5')

    Y_NN = nn_model.predict(X)

    list_nn = []
    for v in Y_NN:
        list_nn.append(np.argmax(v))

    list_nn = np.array(list_nn)

    w_df['rf_pred'] = Y_RF
    w_df['nn_pred'] = list_nn

    w_df = w_df.drop(columns=['svm_pred'])
    # w_df['svm_pred'] = s_classifier.predict(X)
    w_df.nn_pred = w_df.nn_pred.astype(float)

    # Train a new model and check

    """
    Stage 2 Training
    """

    dataset_new = w_df.values

    X_new = dataset_new[:, 1:]
    Y_new = dataset_new[:, 0]

    X_train_new, X_test_new, y_train_new, y_test_new = train_test_split(X_new,
                                                                        Y_new,
                                                                        test_size=.44,
                                                                        random_state=42,
                                                                        stratify=Y_new)

    classifier_new = train_on_random_forest(X_train_new, X_test_new, y_train_new, y_test_new)
    pickle.dump(classifier_new, open(f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_classifier.pkl', 'wb'))

    X_train_new_nn, X_test_new_nn, y_train_new_nn, y_test_new_nn = train_test_split(X_new,
                                                                                    Y_new,
                                                                                    test_size=.42,
                                                                                    random_state=42,
                                                                                    stratify=Y_new)

    # Train on NN
    htt, mdll = train_on_nn_network(X_train_new_nn, X_test_new_nn, y_train_new_nn, y_test_new_nn, 'optimal_nn_model3')
    plot_graph(htt)

    optimal_classifier = pickle.load(
        open(f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_classifier.pkl', 'rb'))

    Y_RF = optimal_classifier.predict(X_new)

    nn_model_optimal = tf.keras.models.load_model(f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_nn_model3.h5')

    Y_NN = nn_model_optimal.predict(X_new)

    list_nn_new = []
    for v in Y_NN:
        list_nn_new.append(np.argmax(v))

    list_nn_new = np.array(list_nn_new)

    w_df = w_df.drop(columns=['rf_pred', 'nn_pred'])

    w_df['rf_pred'] = Y_RF
    w_df['nn_pred'] = list_nn
    w_df.nn_pred = w_df.nn_pred.astype(float)

    """
    Final Training
    """

    dataset_new = w_df.values

    X_final = dataset_new[:, 1:]
    Y_final = dataset_new[:, 0]

    X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(X_final,
                                                                Y_final,
                                                                test_size=.44,
                                                                random_state=42,
                                                                stratify=Y_final)

    classifier_f = train_on_random_forest(X_train_f, X_test_f, y_train_f, y_test_f, estimator=1000)
    pickle.dump(classifier_f,
                open(f'{Config.MODELS_FOLDER}/cefr_prediction/optimal_models/optimal_classifier_final.pkl', 'wb'))

    w_df['rf_pred'] = classifier_f.predict(X_final)
    dataset_new = w_df.values

    X_final = dataset_new[:, 1:]
    Y_final = dataset_new[:, 0]

    X_train_new_nn_f, X_test_new_nn_f, y_train_new_nn_f, y_test_new_nn_f = train_test_split(X_final,
                                                                                            Y_final,
                                                                                            test_size=.44,
                                                                                            random_state=42,
                                                                                            stratify=Y_final)

    # Train on NN
    h, m = train_on_nn_network(X_train_new_nn_f, X_test_new_nn_f, y_train_new_nn_f, y_test_new_nn_f,
                               'optimal_nn_model_final')
    plot_graph(h)
