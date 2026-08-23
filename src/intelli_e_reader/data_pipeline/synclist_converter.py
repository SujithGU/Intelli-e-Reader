import pandas as pd

cols_to_use_2 = ['word', 'pos', 'cefr']

ndf = pd.read_csv('../data/english_profile_scrape.csv', usecols=cols_to_use_2, encoding='latin1')

n_dict = {}

pos_map = {'determiner': 'DET', 'verb': 'VERB', 'noun': 'NOUN', 'adjective': 'ADJ', 'adverb': 'ADV',
           'pronoun': 'PRONOUN',
           'preposition': 'ADP', 'nan': 'NA', '': 'NA', 'None': 'NA',
           'conjunction': 'CONJ', 'exclamation': 'EXC',
           'modal verb': 'MVB', 'auxiliary verb': 'AVB', 'phrase': 'PHR', 'phrasal verb': 'PVB'}
# reference map
cefr_int = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}

# conversion map
conv_map = {1: 'A', 2: 'A', 3: 'B', 4: 'B', 5: 'C', 6: 'C'}

ndf['cefr_avg'] = ndf['cefr'].replace(cefr_int)

ndf['cefr'] = ndf['cefr'].replace(cefr_int).replace(conv_map)

ndf['pos'] = ndf['pos'].replace(pos_map)

word_list = []
pos_lis = []
cefr_avg = []
cefr_level = []

for index in ndf.index:
    if '/' not in str(ndf['word'][index]) and len(str(ndf['word'][index]).split(" ")) == 1:
        word_list.append(ndf['word'][index])

        pos_val = str(ndf['pos'][index]).replace("nan", "NA")
        pos_lis.append(pos_val)

        cefr_level.append(ndf['cefr'][index])
        cefr_avg.append(ndf['cefr_avg'][index])
print(str(ndf['pos'][2]))
# Write to file
final = {'word': word_list, 'pos': pos_lis, 'cefr_int': cefr_avg, 'cefr': cefr_level}
fdf = pd.DataFrame(final)
fdf.to_csv('../data/modified_scrap_data.csv', index=False)

