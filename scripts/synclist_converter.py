import pandas as pd

cols_to_use_2 = ['word', 'pos', 'cefr']

ndf = pd.read_csv('../Data Files/english_profile_scrape.csv', usecols=cols_to_use_2, encoding='latin1')

n_dict = {}

pmap = {'determiner': 'DET', 'verb': 'VERB', 'noun': 'NOUN', 'adjective': 'ADJ', 'adverb': 'ADV', 'pronoun': 'PRONOUN',
        'preposition': 'ADP','nan':'NA','':'NA','None':'NA',
        'conjunction': 'CONJ', 'exclamation': 'NA',
        'modal verb': 'NA', 'auxiliary verb': 'NA', 'phrase': 'NA', 'phrasal verb': 'NA'}
# reference map
cefr_int = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}

# conversion map
conv_map = {1: 'A', 2: 'A', 3: 'B', 4: 'B', 5: 'C', 6: 'C'}

ndf['cefr_avg'] = ndf['cefr'].replace(cefr_int)

ndf['cefr'] = ndf['cefr'].replace(cefr_int).replace(conv_map)

ndf['pos'] = ndf['pos'].replace(pmap)

word_list = []
pos_lis = []
cefr_avg = []
cefr_level = []

for index in ndf.index:
    if '/' not in str(ndf['word'][index]) and len(str(ndf['word'][index]).split(" ")) == 1:
        word_list.append(ndf['word'][index])
        pos_lis.append(str(ndf['pos'][index]))
        cefr_level.append(ndf['cefr'][index])
        cefr_avg.append(ndf['cefr_avg'][index])

# Write to file
final = {'word': word_list, 'pos': pos_lis, 'cefr_int': cefr_avg, 'cefr': cefr_level}
fdf = pd.DataFrame(final)
fdf.to_csv('../Data Files/modified_scrap_data.csv',index=False)

