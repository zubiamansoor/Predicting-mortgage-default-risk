# -*- coding: utf-8 -*-
"""business_hackathon.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SOSvaWUWnE1J5ip9d-z73P7lzrUYEhEN
"""

import pandas as pd
import seaborn as sns
import xgboost as xgb
import matplotlib.pyplot as plt

from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import make_scorer
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

# reusing code from - https://towardsdatascience.com/running-xgboost-on-google-colab-free-gpu-a-case-study-841c90fef101

# Read data in
cust_data_pd = pd.read_csv('/content/CUST_DATASET_ST.csv')
fsa_data_pd = pd.read_csv('/content/FSA_DATASET_ST.csv')
mg_data_pd = pd.read_csv('/content/MG_DATASET_ST.csv')

# Get ratio of default to no
mg_data_pd.groupby('default').agg('count')

# Look at distribution of FSA codes across mortgage holders
mg_data_pd.groupby('FSA').FSA.agg('count')

# Lets join mortgage data with customer data
mg_w_cust_dat_pd = mg_data_pd.merge(cust_data_pd, on='mg_acc', how='left')

# Now lets join FSA to the merged_data
all_dat_pd = mg_w_cust_dat_pd.merge(fsa_data_pd, on='FSA', how='left')

# Add a predictor that computes Loan to value ratio
all_dat_pd['LTR'] = all_dat_pd['purchase_price'] / all_dat_pd['loan_size']

# Convert date column into datetime obj
all_dat_pd['origin_date'] = pd.to_datetime(all_dat_pd['origin_date'], format="%Y-%m-%d")

# Add dummy variables to dataframe
dummy_cols = ['property_type', 'amort_period']
all_dat_w_dummies_pd = pd.get_dummies(all_dat_pd, columns=dummy_cols)

# Remove holdout samples
train_dat_pd = all_dat_w_dummies_pd[all_dat_w_dummies_pd.Sample != 'Holdout']

# Check
train_dat_pd.groupby('Sample').Sample.agg('count')

# Drop join cols to create for feature matrix
drop_cols = ['mg_acc', 'FSA', 'default', 'Sample', 'cust_age', 'cust_gender', 'origin_date']
features_pd = train_dat_pd.drop(columns=drop_cols)

# Create a target column that is categorical/binary
target = train_dat_pd['default']
cat_col = pd.Categorical(target)
target = pd.Series(cat_col.codes)

# split the clean_X into train and test sets
seed = 1958
X_train, X_test, y_train, y_test = train_test_split(features_pd, target, test_size=0.20, 
                                                    random_state=seed, shuffle=True, stratify=target)

# Commented out IPython magic to ensure Python compatibility.
import time
from xgboost import XGBClassifier# create a default XGBoost classifier
model = XGBClassifier(n_estimators=500, random_state=seed)# define the eval set and metric

eval_set = [(X_train, y_train), (X_test, y_test)]
eval_metric = ["auc","error"]# fit the model
# %time model.fit(X_train, y_train, eval_metric=eval_metric, eval_set=eval_set, verbose=False)

# final model assessment
pred_test = model.predict(X_test)
pred_train = model.predict(X_train)

print('Train Accuracy: ', accuracy_score(y_train, pred_train))
print('Test Accuraccy: ', accuracy_score(y_test, pred_test))

print('Classification Report:')
print(classification_report(y_test,pred_test))

# retrieve performance metrics
results = model.evals_result()
epochs = len(results['validation_0']['error'])
x_axis = range(0, epochs)

fig, ax = plt.subplots(1, 2, figsize=(15,5))# plot auc
ax[0].plot(x_axis, results['validation_0']['auc'], label='Train')
ax[0].plot(x_axis, results['validation_1']['auc'], label='Test')
ax[0].legend()
ax[0].set_title('XGBoost AUC-ROC')
ax[0].set_ylabel('AUC-ROC')
ax[0].set_xlabel('N estimators')# plot classification error
ax[1].plot(x_axis, results['validation_0']['error'], label='Train')
ax[1].plot(x_axis, results['validation_1']['error'], label='Test')
ax[1].legend()
ax[1].set_title('XGBoost Classification Error')
ax[1].set_ylabel('Classification Error')
ax[1].set_xlabel('N estimators')
plt.show()
plt.tight_layout()

# Commented out IPython magic to ensure Python compatibility.
# create a default XGBoost classifier
model = XGBClassifier(
    random_state=seed, 
    eval_metric=["error", "auc"]
)

# Create the grid search parameter grid and scoring funcitons
param_grid = {
    "learning_rate": [0.1, 0.01],
    "subsample": [0.6, 0.8, 1.0],
    "max_depth": [2, 3, 4],
    "n_estimators": [100, 200, 500, 600],
    "reg_lambda": [1, 1.5, 2]
}

scoring = {
    'AUC': 'roc_auc', 
    'Accuracy': make_scorer(accuracy_score)
}

# create the Kfold object
num_folds = 5
kfold = StratifiedKFold(n_splits=num_folds, random_state=seed)

# create the grid search object
n_iter=50
grid = RandomizedSearchCV(
    estimator=model, 
    param_distributions=param_grid,
    cv=kfold,
    scoring=scoring,
    n_jobs=-1,
    n_iter=n_iter,
    refit="AUC",
)

# fit grid search
# %time best_model = grid.fit(X_train,y_train)

print(f'Best score: {best_model.best_score_}')
print(f'Best model: {best_model.best_params_}')

# Asses best model's performance on hold out test set
pred_test = best_model.predict(X_test)
pred_train = best_model.predict(X_train)

print('Train Accuracy: ', accuracy_score(y_train, pred_train))
print('Test Accuraccy: ', accuracy_score(y_test, pred_test))

print('\nConfusion Matrix:')
print(confusion_matrix(y_test, pred_test))

print('\nClassification Report:')
print(classification_report(y_test, pred_test))

# Get best model's predictions for holdout set
holdout_pd = all_dat_w_dummies_pd[all_dat_w_dummies_pd.Sample == 'Holdout']

# Drop join cols to create for feature matrix
drop_cols = ['mg_acc', 'FSA', 'default', 'Sample', 'cust_age', 'cust_gender', 'origin_date']
H_test = holdout_pd.drop(columns=drop_cols)

# Remove dropped cols from holdout features
pred_holdout_label = best_model.predict(H_test)
pred_holdout_probs = best_model.predict_proba(H_test)

default_probs = [x[1] for x in pred_holdout_probs.tolist()]

# Add model predictions to dataset with account ids
holdout_pd.loc[:, 'pred_labels'] = pred_holdout_label.tolist()
holdout_pd.loc[:, 'pred_probs'] = default_probs

# Use the highest prediction for an mg account to determine if an account holder will default
H_pred = holdout_pd.groupby('mg_acc').agg('max')

# Summarize predictions
H_pred.loc[:, 'mg_acc'] = H_pred.index
H_pred_small = H_pred

# Append predictions with mortgage ids
keep_cols = ['mg_acc', 'pred_probs', 'pred_labels']
final_preds = H_pred_small[keep_cols].reset_index(drop=True)

final_preds.to_csv('/content/final_predictions.csv')

H_pred_small[keep_cols].reset_index(drop=True)

# store the winning model in a new variable
xgc = best_model.best_estimator_

# saving the feature names to the model
xgc.get_booster().feature_names = features_pd.columns.to_list()

# Create the feature importances plot
fig, ax = plt.subplots(figsize=(15,5))

# plot importances with feature weight
xgb.plot_importance(
    booster=xgc, 
    importance_type='weight',
    title='Feature Weight',
    show_values=False,
    height=0.5,
    ax=ax,
)

# plot importances with split mean gain
# xgb.plot_importance(
#     booster=xgc,
#     importance_type='gain',
#     title='Split Mean Gain',
#     show_values=False,
#     height=0.5,
#     ax=ax[1]
# )

# plot importances with sample coverage
# xgb.plot_importance(
#     xgc,
#     importance_type='cover',
#     title='Sample Coverage',
#     show_values=False,
#     height=0.5,
#     ax=ax[2]
# )
plt.tight_layout()
plt.savefig('/content/feature_importance.png')

