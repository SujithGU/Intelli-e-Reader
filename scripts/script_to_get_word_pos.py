import pandas as pd
import csv
import os
import logging

'''
Script used to 
Read the csv file 'word_pos_master_data.csv' 
1. Average of all the predictions are considered for the final CEFR Level
2. Once the CEFR Level is finalised, using conversion map, CEFR levels are reduced to simpler level
Write to a new csv file 'word_pos_modified_data.csv'
'''
logging.basicConfig(filename='../Data Files/logs/word_pos_master_to_modify_log_file.log',
                    filemode='w',
                    level=logging.DEBUG)

# list of columns to ignore from, word_pos_master_data.csv
cols_to_ignore = ['X2000', 'X2001', 'X2002', 'X2003', 'X2004', 'X2005', 'X2006', 'X2007', 'AvrgOfYears', 'Teachers Avg']

# list of columns to use, from word_pos_master_data.csv
cols_to_use = ['Word', 'PoS', 'Level.Teachers.Average', 'Level.Predicted.RF', 'Level.Predicted.NN',
               'Level.Predicted.SVM']

# reference map
cefr_int = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}

# conversion map
conv_map = {1: 'A', 2: 'A', 3: 'B', 4: 'B', 5: 'C', 6: 'C'}

try:
    df = pd.read_csv('../Data Files/word_pos_master_data.csv', usecols=cols_to_use)

    # change CEFR levels to numbers in order to take avg of 4 Prediction algorithms
    df['Level.Teachers.Average'] = df['Level.Teachers.Average'].replace(cefr_int)
    df['Level.Predicted.RF'] = df['Level.Predicted.RF'].replace(cefr_int)
    df['Level.Predicted.NN'] = df['Level.Predicted.NN'].replace(cefr_int)
    df['Level.Predicted.SVM'] = df['Level.Predicted.SVM'].replace(cefr_int)

    # calculate cefr avg for all rows
    avg_list = []

    # iterate through the data frame and form a dictionary
    for row_index in df.index:
        avg = (df['Level.Teachers.Average'][row_index]
               + df['Level.Predicted.RF'][row_index]
               + df['Level.Predicted.NN'][row_index]
               + df['Level.Predicted.SVM'][row_index]) / 4
        avg_list.append(int(avg))

    # adding 'cefr avg' column
    df['cefr_level_avg'] = avg_list

    # Converting the average values back to new reduced cefr level - A1/A2-> A, B1/B2-> B, C1/C2-> C
    df['cefr_level'] = df['cefr_level_avg'].replace(conv_map)

    new_df = df

    # Removing unwanted cols
    new_df = new_df.drop(['Level.Teachers.Average', 'Level.Predicted.RF', 'Level.Predicted.NN',
                          'Level.Predicted.SVM'], axis=1)

    # renaming to col name to lower case
    new_df = new_df.rename(columns={'Word': 'word', 'PoS': 'pos'})

    if not os.path.isfile('../Data Files/word_pos_modified_data.csv'):
        # Create a new csv with modified columns
        new_df.to_csv('../Data Files/word_pos_modified_data.csv', index=False)
    else:
        os.remove('../Data Files/word_pos_modified_data.csv')
        # Create a new csv with modified columns
        new_df.to_csv('../Data Files/word_pos_modified_data.csv', index=False)
    if len(new_df) == len(df):
        logging.debug("Data Converted successfully")
    else:
        logging.error("Conversion Fail: Check the data set")
except:
    logging.error('Possible read or write error: Examine', sys.exc_info())
