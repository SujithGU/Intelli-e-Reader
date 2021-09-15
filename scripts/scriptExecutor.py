import fetchWordSyns as fws
import csvToJson as c2j
import rankSyns as rs
import json
from pathlib import Path


parentDirPath = Path(__file__).parent.parent
tcl_obj = rs.RankSyns()

# Fetch word syns
# fws_obj = fws.FetchWordSyns()
# fws_obj.main('synonyms')

# convert 2 column CSV to JSON.
# c2j.convertToJsonFile('/', oldFileName='ModelWords_thesaurus.csv',
#                       newFileName='ModelWords_thesaurus.json')

# Retrieve the json data from both the files.
# try:
#     with open(str(parentDirPath) + '/data_files/ModelWords_combined.json', 'r') as json_file:
#         modelwords_json = json.load(json_file)

#     for key in modelwords_json.keys():
#         # print(modelwords_json[key]['synonyms'])
#         distances = tcl_obj.rank_syns(key, modelwords_json[key]['synonyms'])
#         modelwords_json[key]['synonyms'] = distances
#         # print(modelwords_json[key])
#         # print('Key:', key)
#         # print(distances[:4])
#         # print('------------------------------')

#     with open(str(parentDirPath) + '/data_files/' + 'ModelWords_ranked.json', 'w') as outfile:
#         json.dump(modelwords_json, outfile)
#     print('Success: File created')
# except:
#     print('Error in creating file')
