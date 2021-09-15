import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn import metrics
import pickle

# import data
data = pd.read_csv('data_files/user_level_mockdata.csv')

df = data[['Avg_A', 'Avg_B', 'Avg_C', 'Level']]

# define input and output
X = df[['Avg_A', 'Avg_B', 'Avg_C']]
y = df[['Level']]

# split data into train and test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0)
model = RandomForestClassifier(n_estimators=50)

model.fit(X_train, y_train)
try:
    pickle.dump(model, open('UserTestModel.sav', 'wb'))
except:
    print('Error in writing model')

# test model accuracy
y_pred = model.predict(X_test)
