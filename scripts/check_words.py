import pandas as pd

'''
Dummy file to check the numbers. DELETE LATER
'''
cols_to_use = ['Synonyms']

df1 = pd.read_csv('../data_files/word_pos_modified_data.csv')
df2 = pd.read_csv('../data_files/modified_scrap_data.csv')
df = pd.read_csv('../data_files/SynListSynonyms.csv', usecols=cols_to_use)

list_data_1 = list(df1['word'])
list_data_2 = list(df2['word'])
list_data_1.extend(list_data_2)

print(len(df1['word']))
print(len(df2['word']))
n_list = []

for index in df.index:
    strr = df['Synonyms'][index].replace('"', '') \
        .replace('[', '') \
        .replace(']', '') \
        .replace("'", "") \
        .strip() \
        .split(',')
    n_list.extend(strr)

count = 0
for word in n_list:
    if any(word in s for s in list_data_1):
        count += 1

print(len(n_list))
print(count)
