# -*- coding: utf-8 -*-
"""CENG463_project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12bsN_FoX8cjFo470m9yblHVJ4ggcvNZS
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import threading

from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,f1_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn import svm, datasets
from sklearn.neighbors import KNeighborsClassifier


"""train.csv"""

data = pd.read_csv("C:/Users/hp/Desktop/train.csv")


#df_filtered = data.query("`Code` != 0 and `Blue` != 0 and `Red` != 0 and `Green` != 0 and `NIR` != 0")
df_filtered = data[(data['Blue'] != 0) & (data['Red'] != 0) & (data['Green'] != 0) & (data['NIR'] != 0)]
df_filtered = df_filtered[df_filtered['Code'] != 0]


df_normal = df_filtered.copy()

for column in range(2, len(df_normal.columns)):
  df_normal[df_normal.columns[column]] /= 10000



ndvi = (df_normal['NIR'] - df_normal['Red']) / (df_normal['NIR'] + df_normal['Red'])
df_normal = df_normal.assign(NDVI = ndvi)

ndwi = ( df_normal['Green'] - df_normal['NIR']) / (df_normal['NIR'] + df_normal['Green'])
df_normal = df_normal.assign(NDWI = ndwi)
evi = 2.5 * (df_normal['NIR'] - df_normal['Red']) / (df_normal['NIR'] + 2.4 * df_normal['Red'] + 1)
df_normal = df_normal.assign(EVI = evi)

intensity = (df_normal['Red'] * 0.2126 + 0.7152 * df_normal['Green'] + 0.0722 * df_normal['Blue'])
df_normal = df_normal.assign(Intensity = intensity)

df_normal.Code.value_counts()

X = df_normal[['Blue', 'Green', 'Red', 'NIR', 'NDVI', 'NDWI', 'EVI', 'Intensity']]
y = df_normal['Code']


def split_and_train_decision_tree(test_size, random_state, X, y):
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = random_state)
  tree_clf = DecisionTreeClassifier(random_state = random_state)
  tree_clf.fit(X_train, y_train)
  y_pred_test = tree_clf.predict(X_test)
  return f1_score(y_test, y_pred_test, average = 'weighted')

def split_and_train_random_forest(test_size, random_state, X, y, leaf):
      X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = random_state)
      classifier = RandomForestClassifier(min_samples_leaf=leaf)
      classifier.fit(X_train, y_train)
      y_pred_test = classifier.predict(X_test)
      return f1_score(y_test, y_pred_test, average='weighted')

def split_and_train_knn(test_size, random_state, X, y, k):
      X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = random_state)
      knn = KNeighborsClassifier(n_neighbors=k)
      knn.fit(X_train, y_train)
      y_pred_test = knn.predict(X_test)
      return f1_score(y_test, y_pred_test, average="micro")

def go(test_size):
    print("Thread Started")
    global bests
    f1_scores = []
    for j in range(1, 30):
        f1_score_ = split_and_train_random_forest(test_size, 42, X, y, j)
        f1_scores.append({"f1_score": f1_score_, "leaf": j, "test_size": test_size})
        print("test size = %.2f" % test_size, " , Leafs: ", j, "f1_score = ", f1_score_)
    bests.append(max(f1_scores, key=lambda x: x['f1_score']))

bests = []
threads = []


for i in np.arange(0.1, 1, 0.1):
    th = threading.Thread(target=go, args=[i])
    threads.append(th)
    th.start()

for thread in threads:
    thread.join()

with open("bests.txt", "w") as file:
    for best in bests:
        file.write(str(best) + "\n")

data_test = pd.read_csv("C:/Users/hp/Desktop/test.csv")

df_normal_test = data_test.copy()

for column in range(1, len(df_normal_test.columns)):
  df_normal_test[df_normal_test.columns[column]] /= 10000

ndvi_test = (df_normal_test['NIR'] - df_normal_test['Red']) / (df_normal_test['NIR'] + df_normal_test['Red'])
df_normal_test = df_normal_test.assign(NDVI = ndvi_test)

ndwi_test = (df_normal_test['Green'] - df_normal_test['NIR']) / (df_normal_test['NIR'] + df_normal_test['Green'])
df_normal_test = df_normal_test.assign(NDWI = ndwi_test)
evi = 2.5 * (df_normal_test['NIR'] - df_normal_test['Red']) / (df_normal_test['NIR'] + 2.4 * df_normal_test['Red'] + 1)
df_normal_test = df_normal_test.assign(EVI = evi)

intensity = (df_normal_test['Red'] * 0.2126 + 0.7152 * df_normal_test['Green'] + 0.0722 * df_normal_test['Blue'])
df_normal_test = df_normal_test.assign(Intensity = intensity)


df_normal_test = df_normal_test.fillna(value = 0)


def predict_test(predict_data, leaf, test_size):
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = 42)
  tree_clf = RandomForestClassifier(min_samples_leaf=leaf)
  tree_clf.fit(X_train, y_train)
  y_predict = tree_clf.predict(predict_data)
  return y_predict


best_of_bests = max(bests, key= lambda x: x['f1_score'])
print("Pred Start")
prediction = predict_test(df_normal_test[['Blue', 'Green', 'Red', 'NIR', 'NDVI', 'NDWI', 'EVI', 'Intensity']], best_of_bests['leaf'], best_of_bests['test_size'])
print("Test prediction = ", prediction)

final = df_normal_test[["Id"]].copy()
final = final.assign(Code = prediction)


final.to_csv('out.csv', index = False)