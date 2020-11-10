# -*- coding: utf-8 -*-
"""Trabalho_grupo_SR_JA_v2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1p4M45vl8q3QaIPAI6Iqo_2RQ9G4ojkw8

# 0. Set-up
"""

import pandas as pd
import numpy as np
import ast
import seaborn as sns 
import matplotlib.pyplot as plt
plt.rcParams.update({'axes.labelsize':13, 'axes.titlesize':14,'xtick.labelsize':12, 'ytick.labelsize':12})

from sklearn.feature_selection import chi2
from sklearn.preprocessing import MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

SEED = 42

"""**Functions**"""

def adjusted_r2(r2, X):

  return (1 - ((1 - r2)*(X.shape[0] - 1)/(X.shape[0] - X.shape[1] - 1)))

def get_score(y_test, y_prediction, X_test):
    r2 = r2_score(y_test, y_prediction)
    
    r2_adjusted = adjusted_r2(r2, X_test)

    rmse = np.sqrt(mean_squared_error(y_test, y_prediction))
    
    return r2_adjusted, rmse

def my_train_test_split(dataframe):
    data = dataframe.copy(deep=True)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(data.drop(['vote_average'], axis=1), 
                                                        data['vote_average'], test_size = 0.2, 
                                                        random_state=SEED)

    # Normalize
    features_names = X_train.columns

    scaler_X = MinMaxScaler([0,1])
    X_train = pd.DataFrame(scaler_X.fit_transform(X_train), columns = features_names)
    X_test = pd.DataFrame(scaler_X.transform(X_test), columns = features_names)

    scaler_y = MinMaxScaler([0,1])
    y_train = scaler_y.fit_transform(np.array(y_train).reshape(-1,1))
    y_test = scaler_y.transform(np.array(y_test).reshape(-1,1))

    return X_train, X_test, y_train, y_test

def linear_regression_score(df_test):
    
  # Train-test-split 
  X_train, X_test, y_train, y_test = my_train_test_split(df_test)

  # Modelling
  lr = LinearRegression().fit(X_train, y_train)

  y_preds = lr.predict(X_test)
  
  # Metrics evaluation
  r2_adjusted, rmse = get_score(y_test, y_preds, X_test)

  return r2_adjusted, rmse

def get_names(row):
    names=[]
    for dictionary in row:
        names.append(dictionary['name'])
    
    return names

def get_dictionaries(series):
    series = series.apply(lambda row: ast.literal_eval(row)) # transform from string to list 
    series = series.apply(lambda row: get_names(row)) # replace dictionaries by list of names
    
    # Missing values 
    index_na = []
    for index, row in series.iteritems():
        if not row:
            index_na.append(index)

    print('Number of missing values: {}'.format(len(index_na)))
    
    # Values in feature
    unique_list = []
    
    for row in series:
        for name in row:
            if name not in unique_list:
                unique_list.append(name)
    
    return series, unique_list

def encode_data(dataframe):
    data = dataframe.copy(deep=True)
    
    ## Enconding
    # One Hot Enconding 
    for genre in unique_dict['genres']:
        data[genre] = data["genres"].apply(lambda row: 1 if genre in row else 0)
    # drop "genres"
    data = data.drop('genres', axis=1) 

    # Ordinal Encoding
    di_lang = {"en" :1, "fr" :2, "es" :3, "zh" :4, "de" :5, "hi" :6, "ja" :7, "it" :8, "cn" :9, "ko" :10, "ru" :11 }
    data['original_language'] = data['original_language'].map(di_lang)
    data['original_language'] = data['original_language'].fillna(0)
    data['original_language'] = data['original_language'].astype('int64')
    
    encoder = LabelEncoder()
    data['status'] = encoder.fit_transform(data['status'])

    return data

"""**Import**"""

## Import CSV ## 
df = pd.read_csv('tmdb_5000_movies.csv')

"""# 1. Data analysis

**Shape & Target variable**
"""

df.shape

# 19 features and 4803 movies

df.info()

# Target variable: vote_average
# Missing values: overview, homepage, release_date, runtime, tagline 
# 6 numerical features, and the rest are objects

### TARGET VARIABLE: Vote average ##
df['vote_average'].hist()
plt.show()

print(df['vote_average'].describe())

# There are 0.0 values. 
# Most of the values are situated between 5 and 8

df.duplicated().sum()
# No duplicated movies

"""**Categorical features**"""

categorical_features = list(df.select_dtypes('object').columns)
int_features = list(df.select_dtypes('int64').columns)
float_features = list(df.select_dtypes('float64').columns)
numerical_features = int_features+float_features

numerical_features.remove('vote_average')

df[categorical_features].head(3)

# 1. genres, keywords, production_companies, production_countries and spoken_languages features are a list with dictionaries.  
# 2. overview and tagline are text features and need special care 
# 3. homepage, original_title and title should have an unique value for each entry if this proves to be true, we can drop them.
# 4. release_data is a date and should be transformed into something understandable to the model.

# Original language
df['original_language'].value_counts()

# We see that most of he films are english

# Status
df['status'].value_counts().plot.barh()
plt.show()

"""**Numerical features**"""

df[numerical_features].hist(figsize=(10,8)) 
plt.tight_layout()
plt.show()

# 1. Budget, popularity, revenue and vote_count have a very skewed distribution 
#    In order to have more insightful features we can:
#      - transform budget and revenue to a logaritm scale 
#      - bin popularity, runtime and vote_count 
# 2. id should be an unique value for each row. If this proves to be true

corrs = df.corr()
corrs[corrs>0.5]

# We see an high correlation between: popularity, budget, revenue and vote_count. 
# All the four features measure (to a certain extent) measure how mainstream is a movie
# We will only look at feature importance later on, but we can see that none of the features is highly correlated with vote_average

"""# 2. Data Cleaning"""

# By comparing the movies with 0 vote_average and IMBD, it was noticed that 0 values are in fact missing votes. 
# Because of this it was decided to discard these rows 
lines_to_drop = df[(df['vote_average']==0.0)].index
df = df.drop(lines_to_drop, axis=0)

df = df.reset_index(drop=True)

baseline = df.copy(deep=True)

"""**Clean categorical features**

`id`
"""

if 'id' in baseline.columns:
  baseline = baseline.drop('id', axis=1)

"""`genres`, `keywords`, `production_companies`, `production_countries`, `spoken_languages`"""

unique_dict = {}

for feature in ['genres', 'keywords', 'production_companies', 'production_countries', 'spoken_languages']:
    print(feature)
    baseline[feature], unique_dict[feature] = get_dictionaries(baseline[feature])

for feature in ['genres', 'keywords', 'production_companies', 'production_countries', 'spoken_languages']:
    print('{}: {}'.format(feature, len(unique_dict[feature])))

## 'keywords', 'production_companies', 'production_countries', 'spoken_languages' ##
# Since all the other features have an high number of unique values it was decided to drop them for now 
# We would like to revise it them later on:
#   - apply OHE but lower count categories in an 'other' category 
#   - create features: number of keywords, countries, companies, spoken language

if 'keywords' in baseline.columns:
  baseline = baseline.drop(['keywords', 'production_companies', 
                            'production_countries', 'spoken_languages'], axis=1)

"""`homepage`"""

# homepage url does not influence the average vote, but the its existance might influence 

baseline['homepage'] = baseline['homepage'].fillna(0)
baseline.loc[baseline['homepage']!=0, 'homepage'] = 1

"""`title` and `original_title`"""

print('Unique values in title: {:.0%}'.format(df['title'].nunique() / df.shape[0]))
print('Unique values in original title: {:.0%}'.format(df['original_title'].nunique() / df.shape[0]))

# since all the features have unique values we will drop them 
baseline = baseline.drop(['title', 'original_title'], axis = 1)

"""`overview` and `tagline`"""

# Since these features are text and a specific pre-processing is needed it was it was decided to drop them to the baseline

if 'tagline' in baseline.columns:
    baseline = baseline.drop(['overview', 'tagline'], axis=1)

"""`release_date`"""

# This feature will be treated in the section feature engineering. For now we will drop it: 
baseline = baseline.drop(['release_date'], axis=1)

"""**Missing values**"""

baseline.isna().sum()

# runtime has a missing value

baseline['runtime'].hist()
plt.show()

baseline['runtime'] = baseline['runtime'].fillna(baseline['runtime'].mean())

"""`budget`"""

# Missing values 
# Since there famous movies with budget=0. It is concluded that budget==0 is a missing value 
print('Percentage of missing values in budget? {:.0%}'.format(baseline.loc[baseline.budget==0, 'budget'].count() / baseline.shape[0]))

# Fill NaN with the mean
baseline['budget'] = baseline['budget'].replace(0,np.NaN)
baseline['budget'] = baseline['budget'].fillna(baseline['budget'].mean())

"""`revenue`"""

# Missing values 
print('Percentage of missing values in revenue? {:.0%}'.format(baseline.loc[baseline.revenue==0, 'revenue'].count() / baseline.shape[0]))
# Although 29% of missing values is a significant percentage of missing values,
# we have decided to keep the variable and fill them with the mean

baseline['revenue'] = baseline['revenue'].replace(0,np.NaN)
baseline['revenue'] = baseline['revenue'].fillna(baseline['revenue'].mean())

"""# 3. Baseline Score

> **Note on model evaluation**
>
> In this problem a deviation on `vote_average` of 0.1 is not relevant, but to a deviation of 1.0 is. In order to try to achieve the best model we have choose to study $RMSE$ since this is a metric that penalizes higher deviations of the model. \
Furthermore, $RMSE$ as is smoothly differentiable it is easier to handle by the model, this is, faster to compute. E.g.: When computing a decision tree, it was noticed that when `criterion = 'mae'`, its computation was much slower than when `criterion = 'mse'` 
>
>Besides $RMSE$ it was also choosen to study the *adjusted* $R^2$. This is a metric that measures how much the features explain the variability of the `vote_average` with a certain model. In contrast with $R^2$, the *adjusted* $R^2$ is independent on the number of model terms.
"""

baseline_encoded = encode_data(baseline)
X_train, X_test, y_train, y_test = my_train_test_split(baseline_encoded)

lr = LinearRegression().fit(X_train, y_train)
y_preds = lr.predict(X_test)

r2_adjusted_baseline, rmse_baseline = get_score(y_test, y_preds, X_test)

print('R2 adjusted of baseline = {:.2%}'.format(r2_adjusted_baseline))
print('RMSE of baseline = {:.2%}'.format(rmse_baseline))

"""# 4. Feature Engineering

`release_date`
"""

df_1 = baseline_encoded.copy(deep=True)
df_original = df.copy(deep=True)

# from date we will extract year and quarter 

# datetime format:
df_1['release_date'] = pd.to_datetime(df_original['release_date'], infer_datetime_format=True)

# create features:
df_1['release_year'] = df_1['release_date'].dt.year.astype('Int64')
df_1['release_quarter'] = df_1['release_date'].dt.quarter

#Fill nan
df_1['release_year'] = df_1['release_year'].fillna(df_1['release_year'].mode()[0])
df_1['release_year'] = df_1['release_year'].astype('int64')
df_1['release_quarter'] = df_1['release_quarter'].fillna(df_1['release_quarter'].mode()[0])

# drop release_date:
if 'release_date' in df_1.columns:
    df_1 = df_1.drop('release_date', axis=1)

r2_adj_1, rmse_1 = linear_regression_score(df_1)
print('R2 adjusted = {:.2%}; Difference to baseline = {:.2}'.format(r2_adj_1, (r2_adj_1 - r2_adjusted_baseline)*100))
print('RMSE = {:.3%}'.format(rmse_1))

"""When handling the release_date, by identifying the year and the quarter, the model improved significantly.

`original_title`
"""

df_2 = df_1.copy(deep=True)

# but before we will create a new feature that carries the information that a movies has changed title 

# Create 'changed_title' feature:
df_2['changed_title'] = df_original['title'].eq(df_original['original_title']) 
df_2['changed_title'] = df_2['changed_title'].fillna(0)
map_changed_title = {True:0, False:1}

df_2['changed_title'] = df_2['changed_title'].map(map_changed_title).astype('int64')

df_2['changed_title'].value_counts()

# Drop title, original_title:
if 'title' in df_2.columns:
  df_2 = df_2.drop(['title', 'original_title'], axis=1)

r2_adj_2, rmse_2 = linear_regression_score(df_2)
print('R2 adjusted = {:.2%}; Difference to previous = {:.2}'.format(r2_adj_2, (r2_adj_2 - r2_adj_1)*100))
print('RMSE = {:.3%}'.format(rmse_2))

"""Both R2 adjusted and RMSE have improved slightly

`runtime`
"""

df_3 = df_2.copy(deep=True)

print('Number of value with high values of runtime (>200): {}'.format(df_3.loc[df_3['runtime']>200, 'runtime'].count()))

# Bin "runtime" values > 200
df_3.loc[df_3['runtime']>200, 'runtime'] = 200
df_3['runtime'] = df_3['runtime'].fillna(df_3['runtime'].mean())

df_3['runtime'].hist()
plt.show()

r2_adj_3, rmse_3 = linear_regression_score(df_3)
print('R2 adjusted = {:.2%}; Difference to previous = {:.2}'.format(r2_adj_3, (r2_adj_3 - r2_adj_2)*100))
print('RMSE = {:.3%}'.format(rmse_3))

"""We can see that treating outliers improved the model performace slighly.

`vote_count`
"""

df_4 = df_3.copy(deep=True)

print('Number of value with high values of vote_count (>8000): {}'.format(df_4.loc[df_4['vote_count']>8000, 'vote_count'].count()))

# Bin "vote_count" values > 8000
df_4.loc[df_4['vote_count']>8000, 'vote_count'] = 8000

df_4['vote_count'].hist()
plt.show()

r2_adj_4, rmse_4 = linear_regression_score(df_4)
print('R2 adjusted = {:.2%}; Difference to previous = {:.4}'.format(r2_adj_4, (r2_adj_4 - r2_adj_3)*100))
print('RMSE = {:.3%}'.format(rmse_4))

"""The current transformation had a positive impact in the performance

`revenue`
"""

df_5 = df_4.copy(deep=True)

# Fill NaN with the mean
df_5['revenue_log'] = df_5['revenue'].replace(0,np.NaN)
df_5['revenue_log'] = df_5['revenue_log'].fillna(df_5['revenue_log'].mean())
df_5 = df_5.drop('revenue', axis=1)

# Transform to log 
df_5['revenue_log'] = np.log(df_5['revenue_log'])
df_5['revenue_log'].hist()
plt.show()

r2_adj_5, rmse_5 = linear_regression_score(df_5)
print('R2 adjusted = {:.2%}; Difference to previous = {:.4}'.format(r2_adj_5, (r2_adj_5 - r2_adj_4)*100))
print('RMSE = {:.3%}'.format(rmse_5))

"""R2 adjusted increased slightly so we will discard this transformation

`popularity`
"""

df_6 = df_4.copy(deep=True)

print('Number of value with high values of popularity (>120): {}'.format(df_6.loc[df_6['popularity']>120, 'vote_average'].count()))

# We will bin all the values greater that 200:
df_6.loc[df_6['popularity']>120, 'popularity'] = 120

# Histogram
df_6['popularity'].hist()
plt.show()

r2_adj_6, rmse_6 = linear_regression_score(df_6)
print('R2 adjusted = {:.2%}; Difference to previous = {:.4}'.format(r2_adj_6, (r2_adj_6 - r2_adj_4)*100))
print('RMSE = {:.3%}'.format(rmse_6))

"""The model perfomance improved

### Excluded variables: 
'keywords', 'production_companies',                      'production_countries', 'spoken_languages'

Initially we discard the following variables 'keywords', 'production_companies', 'production_countries', 'spoken_languages', however they may help to improve our model. However, it would be necessary to perform the transformations made to the feature genres, where we were going to verify the existence of unique values by creating a feature for each type. When performing the operation, we apply the One Hot Encoding technique, thus converting categorical features into something that the algorithms can understand.

### Handling categorical features
Initially we have discard the features: `keywords`, `production_companies`, `production_countries`, `spoken_languages`. In order to include them it would be necessary to perform the following steps:
1. identify each unique value
2. rank by `value_counts` and join all low values in a category "others"
3. convert an object feature into a binary by performing One Hot Encoding
4. apply PCA to reduce the dataframe dimensionality

### Handling text features
In order to extract a meaning from text that a machine can understand one must treat these features in a specific way.

Here we will leave some suggestions on how to deal with them

**N-grams vectorizers**

The text can be understood by the type and number of words that happear on that same text. Example: "This was the best concert ever! The music was touching and the spetacule was amazing! Sereasly awesome!" 

The words 'best', 'amazing' and 'awesome' are sinomous (==good) and from those we can access that the person was really happy with the concert even without looking at the grammatical context. So for example if we had a model to classify good and bad concerts, we would have a 3 (number of words) on the feature `good`. 

To be able to do this analysis one should: 
1. Clean the text feature: 
  - make all words lowercase, 
  - tokenize (split all the words)
  - remove ponctuation
  - transform a word into the root form
      - E.g.: playing, plays and played have all the same root word play

2. Vectorize: 
  - Remove stopwords
      - stopwords are words that are so common that do not carry interst to the model. 
      - E.g.: 'the', 'and', 'or', 'an', 'a', etc
  - Build dataframe with the words (or two-words, three-words) features and count. 
      - Words are features and each entry represent the number of times it happears in the text.
  - Normalize with TF-IDF

3. Dimensionality reduction 
  - Usually PCA is the method of choice: 
      - It normally allows to find smaller space than feature selection methods 
      - Usually loss of interpretability is not a limiting factor in NLP

**Neural Networks**

With neural networks we define a voculabulary and a vector for each word it in. These vocabularies are already pre-defined (trained a priori) and accessed through libraries. 

The steps to analyse with neural networks is: 
1. Clean text feature
2. Tag each token 
    - This is done recorring to a library (e.g.: spaCy)
    - A tag can be 'country', 'person', 'sentiment', 'noun', etc
3. Calculate word vectors: 
    - How close is a word from another in the dictionary? 
    - Word vectores can be calculating using an algorithm like word2vec
4. Run neural network

# 5. Modeling
"""

X_train, X_test, y_train, y_test = my_train_test_split(df_6)

"""### Linear Regression"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# lr = LinearRegression()
# 
# parameters = {'fit_intercept':[True,False]}
# 
# clf_lr = GridSearchCV(lr, parameters, cv = 5, scoring='r2').fit(X_train, y_train)
# 
# print("Best estimator:", clf_lr.best_params_)
# 
# # Predict vote_average 
# y_preds = clf_lr.predict(X_test)

r2_adjusted, rmse = get_score(y_test, y_preds, X_test)

print("R^2 adjusted = {:.2%}".format(r2_adjusted))
print("RMSE = {:.2%}".format(rmse))

"""### Non-linear regression"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# 
# r2_adjusted = []
# for n in range(1,4):
#   simple_poly = Pipeline( steps = [('poly', PolynomialFeatures(degree = n)),
#                                    ('linear', LinearRegression())])
# 
#   simple_poly_model = simple_poly.fit(X_train, y_train)
# 
#   y_preds = simple_poly_model.predict(X_test)
# 
#   r2_adjusted.append(get_score(y_test, y_preds, X_test)[0])

pd.Series(r2_adjusted, index = ['Linear', 'Quadratic', 'Cubic'] )

"""The only model with a coherant value is the linear relation.

### KNN
"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# knn = KNeighborsRegressor()
# 
# parameters = {'n_neighbors': range(25, 60, 1)}
# 
# clf_knn = GridSearchCV(knn, parameters, cv = 5, scoring = 'r2').fit(X_train, y_train)
# 
# print("Best estimator:", clf_knn.best_params_)
# clf_knn.best_score_

clf_knn.best_estimator_.n_neighbors

knn = KNeighborsRegressor(n_neighbors =clf_knn.best_estimator_.n_neighbors).fit(X_train, y_train)

y_preds = knn.predict(X_test)

r2_adjusted, rmse = get_score(y_test, y_preds, X_test)

print("R^2 adjusted = {:.2%}".format(r2_adjusted))
print("RMSE = {:.2%}".format(rmse))

"""KNN performed much worse than linear regression.

### SVM
"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# 
# svr = SVR()
# 
# parameters = {'kernel' : ('linear', 'rbf'),'C' : [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]}
# 
# clf_svr = GridSearchCV(svr, parameters, cv = 5, scoring = 'r2').fit(X_train, y_train.ravel())
# 
# print("Best estimator:", clf_svr.best_params_)
# # Predict vote_average 
# y_preds = clf_svr.predict(X_test)

r2_adjusted, rmse = get_score(y_test, y_preds, X_test)

print("R^2 adjusted = {:.2%}".format(r2_adjusted))
print("RMSE = {:.2%}".format(rmse))

"""Despite the computation time being higher, the model performed worse than linear regression

### Decision Tree
"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# tree = DecisionTreeRegressor(random_state=SEED, criterion='mse')  
# # Criterion = 'mse' was choosen in order to minimize RMSE
# 
# parameters = {'max_depth':[3,6,9], 'min_samples_split':[2,4,10]}
# 
# regressor_tree = GridSearchCV(tree, parameters, cv = 5, scoring = 'r2').fit(X_train, y_train)
# 
# print("Best estimator:", regressor_tree.best_params_)
# 
# # Predict vote_average 
# y_preds = regressor_tree.predict(X_test)

r2_adjusted, rmse = get_score(y_test, y_preds, X_test)

print("R^2 adjusted = {:.2%}".format(r2_adjusted))
print("RMSE = {:.2%}".format(rmse))

"""Similarly with KNN, decision tree performed badly.

### Random Forest Tree
"""

# Commented out IPython magic to ensure Python compatibility.
# %%time
# random_forest = RandomForestRegressor(random_state = SEED, criterion='mse')
# 
# parameters = {'n_estimators':[10, 100, 300, 1000], 'max_depth':[3,6], 
#               'min_samples_split':[2, 4, 10]}
# 
# regressor_random = GridSearchCV(random_forest, parameters, cv = 5, scoring = 'r2').fit(X_train, y_train.ravel(), )
# 
# print("Best estimator:", regressor_random.best_estimator_)
# 
# # Predict vote_average 
# y_preds = regressor_random.predict(X_test)

r2_adjusted, rmse = get_score(y_test, y_preds, X_test)

print("R^2 adjusted = {:.2%}".format(r2_adjusted))
print("RMSE = {:.2%}".format(rmse))

"""Despite the high computation time, Random Forest Tree performed worse than Linear Regression

### Neural Networks
"""

mlp = MLPRegressor(solver = 'lbfgs', max_iter = 1200, random_state = SEED, verbose = True)
# We have choose 'lbfgs' solver because this is a small data set 
# and, a big max_iter value because we do not want that MLPRegressor to stop iterating before converging

# Commented out IPython magic to ensure Python compatibility.
# %%time
# ### 1. Hypertunning ###
# parameters = {'hidden_layer_sizes': [(20,), (20,10), (20,10,2), (30,), (30,10), (30,15), (30, 10, 2)], 
#               'learning_rate_init': [0.0001, 0.001, 0.01, 0.1]}
# 
# regressor_mlp = GridSearchCV(mlp, parameters, cv = 5, scoring = 'r2').fit(X_train, y_train.ravel())

print('Best estimator:', regressor_mlp.best_estimator_)

y_preds = regressor_mlp.predict(X_test)
r2, mae = get_score(y_test, y_preds, X_test) 

print("\n\n")
print("R^2 adjusted= {:.2%}".format(r2))
print("RMSE = {:.2%}".format(mae))

"""Although NNA takes longer to compute, it also the model with best R2 adjusted and RMSE performance.

# 5. Feature Selection

The model that performed best was Neural Networks. Since NNA does not hold interpretability and we would like to improve its performance, we will try to do a feature extration with PCA:
"""

n_features = len(list(df_6.columns))

r2_adj = []
rmse = []

for n in range(1,n_features): 
  pipe = Pipeline([
                 ('scaler', MinMaxScaler()),
                 ('PCA', PCA(n_components = n , random_state=SEED)), 
                 ('model', MLPRegressor(solver = 'lbfgs', max_iter = 1200, 
                                        hidden_layer_sizes=(20, 10),
                                        learning_rate_init=0.0001,
                                        random_state = SEED))])

  data_pip_transform = pipe.fit(X_train, y_train.ravel())

  pipe_pred=pipe.predict(X_test)

  r2_adj.append(get_score(y_test, pipe_pred, X_test)[0])
  rmse.append(get_score(y_test, pipe_pred, X_test)[1])

f,(ax1, ax2) = plt.subplots(1,2, figsize=[9,4])
ax1.plot(r2_adj)
ax1.set_ylabel('R2 adjusted')
ax1.set_xlabel('Number of features')

ax2.plot(rmse)
ax2.set_ylabel('RMSE')
ax2.set_xlabel('Number of features')

plt.tight_layout()

"""We can see that both metrics are better with the complete dataframe.

# Perguntas: 

    1. Quantos filmes existem no dataset? E quantas features?
    2. Existem variáveis que não são independentes entre si?
    3. Qual a técnica de regressão que levou a melhores resultados?
    4. Quais os factores que mais contribuem para o sucesso de um filme?
    5. Recomendariam o vosso modelo a uma produtora de filmes?

**Pergunta 1:** \
Existem 4803 filmes e 19 features

**Pergunta 2:** \
Para estudar a **independência das features categóricas**, computou-se $\chi^2$ para todas as relações entre features. 

Hipótese nula: Ambas as variáveis são independentes.\
Se p-value<0.05 então podemos excluir essa hipótese, ou seja a variáveis com baixo p-value são dependentes.
"""

df_6['homepage'] = df_6['homepage'].astype('int64')

# Chi2 hypothesis: "The variables are independent"
cat_features = list(df_6.select_dtypes('int64').columns)
cat_features.remove('vote_count')

chi = {}
pval = {}

for feature in df_6[cat_features]: 
    pval[feature] = chi2(df_6[cat_features], df_6[feature])[1]
    chi[feature] = chi2(df_6[cat_features], df_6[feature])[0]

df_chi = pd.DataFrame(chi, index = cat_features)
df_pval = pd.DataFrame(pval, index = cat_features)

df_pval_masked = df_pval[df_pval<0.05]
plt.figure(figsize = (12,12))
sns.heatmap(df_pval_masked, vmax = 0.05, cmap = 'viridis')
plt.title('Chi2 test with p-value < 0.05')
plt.show()

"""Pode ver-se que há bastantes variáveis dependentes segundo o teste de $\chi^2$. 

Os géneros de cada filme (ex.: thriller, crime, drama, etc), estão particularmente interligados entre si. Por exemplo  *Romance* é independente de *Fantasy*, *Western*, *History* e *War*, e dependente de todos os outros géneros de filme. Ou seja, cada filme tem várias tags de géneros e por isso estes estão bastante dependentes uns do outros. 

Para podemos melhor avaliar o data set iremos deixar essas features género de parte:
"""

features_to_remove = ['Action', 'Adventure', 'Fantasy',  'Science Fiction', 'Thriller',  'Animation', 'Family',  'Western', 'Comedy',  'Romance', 
                     'Horror', 'Mystery',  'History',  'War',  'Music',  'Documentary', 'Crime', 'Horror', 'Drama', 'TV Movie'] # Foreign was left

cat_features2 = [feature for feature in cat_features if feature not in features_to_remove]

chi = {}
pval = {}

for feature in df_6[cat_features2]: 
    pval[feature] = chi2(df_6[cat_features2], df_6[feature])[1]
    chi[feature] = chi2(df_6[cat_features2], df_6[feature])[0]

df_chi = pd.DataFrame(chi, index = cat_features2)
df_pval = pd.DataFrame(pval, index = cat_features2)

df_pval_masked = df_pval[df_pval<0.05]
plt.figure(figsize = (5,5))
sns.heatmap(df_pval_masked, vmax = 0.05, cmap = 'viridis')
plt.title('Chi2 test with p-value < 0.05')
plt.show()

"""Podemos observar que: 
 - `original_language`, `Foreign` e `changed_title` são variáveis dependentes.  
 - `release_year` é dependente de `homepage`, dado que filmes mais velhos não têm homepage.
 - `status` e `release_quarter`não tem dependência com nenhuma das restantes variáveis.

Para além das variáveis categóricas também podemos analisar a **correlação entre as variáveis numéricas**:
"""

numerical_features = list(df_6.select_dtypes('float64').columns)
numerical_features.append('vote_count')
numerical_features.append('release_year')

numerical_features.remove('vote_average')

corrs = df_6[numerical_features].corr()
corrs = corrs[corrs>0.5]
spears = df_6[numerical_features].corr(method='spearman')
spears = spears[spears>0.5]

f,(ax1, ax2) = plt.subplots(1,2, figsize=[12,6])
fig1 = sns.heatmap(corrs, vmin = 0, cmap = "RdBu_r", ax = ax1, annot=True)
fig1.set_title('Features with pearson correlation > 0.5')
fig2 = sns.heatmap(spears, vmin = 0, cmap = "RdBu_r", ax=ax2, annot=True)
fig2.set_title('Features with spearman correlation > 0.5')
plt.tight_layout()
plt.show()

"""Podemos observar que:
- há uma forte correlação (>0.8) entre `vote_count` e `popularity`.
- `revenue` tem uma correlação de aproximadamente 0.7 com `budget` e `vote_count`

**Pergunta 3:**\
A técnica de regressão que levou a melhores resultados foi *Neural Networks* com um R2 adjusted de 44.0% e RMSE de 7.7%. Por este motivo, e por acreditar que a interpretabilidade do modelo não é um factor decisivo, *Neural Networks* foi eleito como o modelo final.

**Pergunta 4:** 

Infelizmente a técnica de Neural Networks não nos permite entender as features de maior importancia. Para termos uma estimativa das features mais importantes iremos:
- Perceber quais as features que apresenta, maiores coeficientes de regressão linear. 
- Quais as features com maiores índices de pureza (Gini)
"""

## Linear coefficient
linear_regression = LinearRegression(**clf_lr.best_params_).fit(X_train, y_train)
pd.Series(linear_regression.coef_.tolist()[0], index=X_train.columns).sort_values(ascending=False).head(10)

## Gini 
random_forest_tree = RandomForestRegressor(**regressor_random.best_params_).fit(X_train, y_train.ravel())
pd.Series(random_forest_tree.feature_importances_, index = X_train.columns).sort_values(ascending=False).head(10)

"""Embora cada critério dê uma importância diferente a cada feature, podemos dizer que as `runtime`, `vote_count`, `popularity`,  `Drama`, `Documentary` são bastante importantes para o modelo.

Se a interpretação do modelo fosse imprescendível ao negócio, então a técnica de Regressão Linear seria escolhida como o modelo final. \
Neste cenário as features mais importantes para o sucesso do filme são: `status`, `vote_count`, `runtime`, `popularity` e `Documentary`

**Pergunta 5:** \

Embora o erro médio do modelo (RMSE) não seja alto, não podemos recomendar um modelo que explica apenas 44% da variação dos dados (R2 adjusted). \
Por falta de tempo grande parte do dataset foi excluído, nomeadamente features como `production_companies` e `keywords` que podem ter um grande impacto no modelo final. Acreditamos por isso, que poderíamos obter um modelo melhor com a introdução de todas as features e a extração destas com PCA.
"""

