import json
import csv
from pathlib import Path

path = Path(__file__).parent.parent

# Converts 2 column CSV to JSON.
def convertToJsonFile(relPath, oldFileName, newFileName):
    try:
        # Read csv file.
        with open(str(path) + relPath + oldFileName) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            wordSynDict = {}
            for row in csv_reader:
                if line_count > 1:
                    rowObj = {
                        # key is the word and value is the synonyms as a list.
                        row[0]: row[1][1:-1].replace('\'','').split(',')
                    }
                    wordSynDict.update(rowObj)
                line_count += 1

        # Write to a new file.
        try:
            with open(str(path) + relPath + newFileName, 'w') as outfile:
                json.dump(wordSynDict, outfile)
            print('Success: File created')
        except:
            print('Error in creating file')

    except:
        raise Exception('File does not exist')


# Converts 4 column CSV to JSON. - word - pos - cefr_int - cefr
def convert_to_json(relPath, oldFileName, newFileName):
    try:
        word_pos_dict = {}
        with open(str(path) + relPath + oldFileName) as csv_file:
            csv_reader = csv.DictReader(csv_file)

            for rows in csv_reader:
                key = rows['word']
                word_pos_dict[key] = rows

        try:
            with open(str(path) + relPath + newFileName, 'w') as outfile:
                json.dump(word_pos_dict, outfile)
            print('Success: File created')
        except:
            print('Error in creating file')

    except:
        raise Exception('File does not exist')


'''
Un-comment the following line to generate cefr json
'''
# convert_to_json('/Data Files/', oldFileName='master_cefr.csv',newFileName='master_cefr.json')

convertToJsonFile('/Data Files/', oldFileName='SynListSynonyms.csv', newFileName='SynonymsDict.json')