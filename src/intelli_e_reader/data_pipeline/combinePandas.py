from pathlib import Path
import json
import pandas as pd

# Gets path to the root directory of the repository.
parentDirPath = Path(__file__).parent.parent

syn_pd = pd.read_csv('ModelWords_synonyms.csv')
thes_pd = pd.read_csv('ModelWords_thesaurus.csv')

# with open(str(parentDirPath) + '/ModelWords_synonyms.json', 'r') as jsonFile:
#     modelwords_syn = json.load(jsonFile)

# with open(str(parentDirPath) + '/ModelWords_thesaurus.json', 'r') as jsonFile:
#     modelwords_thes = json.load(jsonFile)

with open(str(parentDirPath) + '/data/master_cefr.json', 'r') as jsonFile:
    master_cefr_json = json.load(jsonFile)

# Convert str of list format into list


def str_to_list(strVal):
    return strVal[1:-1].replace("'", "").replace(" ", "").strip().split(",")


combined_dict = dict()
for index, row in syn_pd.iterrows():
    key = row['Word']
    syns = str_to_list(row['Synonyms'])
    if key in thes_pd.values:
        thes_row = thes_pd[thes_pd['Word'] == key]
        # thes_row = thes_pd.loc[thes_pd['Word'] == key]
        thes_syns = str_to_list(thes_row.iloc[0]['Synonyms'])
        in_syns = set(syns)
        in_thes = set(thes_syns)
        # Get elements present in thes that are not in syns.
        diff = in_thes - in_syns
        result = syns + list(diff)
        combined_dict[key] = {
            'synonyms': result,
            'level': row['Level']
        }
    else:
        combined_dict[key] = {
            'synonyms': syns,
            'level': row['Level']
        }

print('Extra keys:')
# For extra keys in thesaurus
for index, row in thes_pd.iterrows():
    key = row['Word']
    syns = str_to_list(row['Synonyms'])
    if combined_dict.get(key) is None:
        if key in syn_pd.values:
            syn_row = syn_pd[syn_pd['Word'] == key]
            thes_syns = str_to_list(syn_row.iloc[0]['Synonyms'])
            in_syns = set(syns)
            in_thes = set(thes_syns)
            # Get elements present in thes that are not in syns.
            diff = in_thes - in_syns
            result = syns + list(diff)
            combined_dict[key] = {
                'synonyms': result,
                'level': row['Level']
            }
        else:
            combined_dict[key] = {
                'synonyms': syns,
                'level': row['Level']
            }

try:
    with open(str(parentDirPath) + '/data/' + 'ModelWords_combined.json', 'w') as outfile:
        json.dump(combined_dict, outfile)
    print('Success: File created')
except:
    print('Error in creating file')
