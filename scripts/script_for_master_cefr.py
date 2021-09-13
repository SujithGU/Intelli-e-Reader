import pandas as pd
import collections
import math

"""
Generate CEFR Master set and corresponding JSON file for the same
"""

df_eng = pd.read_csv("../data_files/modified_scrap_data.csv")
df_teacher = pd.read_csv("../data_files/word_pos_modified_data.csv")

list1 = []
list2 = []

for index in df_eng.index:
    list1.append(df_eng["word"][index] + "_" + str(df_eng["pos"][index]).upper())

for index in df_teacher.index:
    list2.append(df_teacher["word"][index] + "_" + str(df_teacher["pos"][index]).upper())

df_eng["word_pos_combined"] = list1
df_teacher["word_pos_combined"] = list2

# combine duplicate word_pos values in list
duplicate_eng = []
duplicate_teachers = []

# find duplicates
[duplicate_eng.append(item) for item, count in collections.Counter(list1).items() if count > 1]

[duplicate_teachers.append(item) for item, count in collections.Counter(list2).items() if count > 1]

sorted(duplicate_teachers)
sorted(duplicate_eng)

print(f"Size of teacher list {len(duplicate_teachers)} ")
print(f"Size of eng list {len(duplicate_eng)} ")

dictionary_teachers = {}
dictionary_eng = {}

# combine duplicates from the same file
for word in duplicate_teachers:
    sum_val = 0
    count = 0
    for index in df_teacher.index:
        if word is df_teacher["word_pos_combined"][index]:
            sum_val += df_teacher["cefr_level_avg"][index]
            count += 1
    dictionary_teachers[word] = str(int(math.floor(sum_val / count)))

print(f"Size of teacher dict {len(dictionary_teachers)} ")
for word in duplicate_eng:
    sum_val = 0
    count = 0
    for index in df_eng.index:
        if word is df_eng["word_pos_combined"][index]:
            sum_val += df_eng["cefr_int"][index]
            count += 1
    dictionary_eng[word] = str(int(math.floor(sum_val / count)))
print(f"Size of eng dict {len(dictionary_teachers)} ")

modified_dict_eng = {}
modified_dict_teachers = {}

for index in df_teacher.index:
    word_pos = df_teacher["word_pos_combined"][index]
    if word_pos not in dictionary_teachers:
        cefr = df_teacher["cefr_level_avg"][index]
        modified_dict_teachers[word_pos] = cefr
    else:
        cefr = dictionary_teachers.get(word_pos)
        modified_dict_teachers[word_pos] = cefr
print(f"Size of combined teacher list {len(modified_dict_teachers)} ")

for index in df_eng.index:
    word_pos = df_eng["word_pos_combined"][index]
    if word_pos not in dictionary_eng:
        cefr = df_eng["cefr_int"][index]
        modified_dict_eng[word_pos] = cefr
    else:
        cefr = dictionary_eng.get(word_pos)
        modified_dict_eng[word_pos] = cefr
print(f"Size of combined eng list {len(modified_dict_eng)} ")

# combine data from 2 sets with no duplicates
# Prioritizing values in modified_dict_eng

for key, value in modified_dict_teachers.items():
    if key not in modified_dict_eng:
        modified_dict_eng[key] = value

print(f"Size of new combined eng list {len(modified_dict_eng)} ")

# Saving Data to csv

list_word = []
list_pos = []
list_cefr_int = []
list_cefr = []
# conversion map
conv_map = {1: 'A', 2: 'A', 3: 'B', 4: 'B', 5: 'C', 6: 'C'}

for key, value in modified_dict_eng.items():
    val = key.split("_")
    list_word.append(val[0])
    list_pos.append(val[1])
    list_cefr_int.append(str(value).strip())
    list_cefr.append(conv_map.get(int(str(value).strip())))

final = {'word': list_word, 'pos': list_pos, 'cefr_int': list_cefr_int, 'cefr': list_cefr}
fdf = pd.DataFrame(final)
fdf.to_csv('../data_files/master_cefr.csv', index=False)
