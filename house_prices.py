# -*- coding: utf-8 -*-
from google.colab import drive
drive.mount('/content/gdrive/')

!pip install scikit-learn==0.24

#importing libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns
from sklearn.model_selection import cross_validate
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.model_selection import RandomizedSearchCV
from sklearn.linear_model import LassoCV, Lasso
from sklearn.feature_selection import SelectFromModel,  VarianceThreshold, SequentialFeatureSelector

"""a)

"""

np.random.seed(42) #setting a seed, just in case that we may need it later
try:
  data_set = np.load('dataset.npz')  #TODO cleanup
except:
  pass
try:
  data_set = np.load(r"D:\Downloads\dataset.npz") #loading the data
except:
  pass

df = pd.DataFrame(data=data_set['X'], columns=data_set['features']) #extracting the data to a dataframe
df['price'] = data_set['y']

#Now a short EDA
print("Number of rows: {0:,}".format(len(df)))
print("Number of columns: {0:,}".format(len(df.columns)))

display(df.head())
print('\n Data Types:')
print(df.dtypes)


def color(val): #to get some nice colors in the pandas dataframe for missing values
    color = "green"
    if val > 0:
        color = "lightcoral"
    if val > 10:
        color = "red"
    return 'background-color: %s' % color

describe = df.describe().transpose() #aggregating important data statistics
null_values = pd.DataFrame(df.isna().sum()).rename(columns={0:"num missing"}, inplace=False) 
null_values["pct missing in data"] = null_values["num missing"] / len(df) * 100 #calculate percentage of null values

describe_null = describe.join(null_values, how="left")

display(describe_null[["count", "min", "25%", "mean", "50%", "75%", "max", "std", "pct missing in data"]].round(3).style.applymap(color, subset=["pct missing in data"]))


def display_distribution(values_in, title, min_value=None, max_value=None):
    """Plot histograms of the data"""
    values = list(values_in.dropna())
    
    num_bins   = min(20, len(set(values)))
    log_prefix = ""
    
    if min_value != None:
        values = [max(min_value,x) for x in values]
    if max_value != None:
        values = [min(max_value,x) for x in values]
    
    if (min(values) > 0) & ((np.mean(values) > 2*np.median(values)) | (np.mean(values) < .75*np.median(values))):
        log_prefix = "Log of Values"
        values     = [np.log(x) for x in values] 
        
    plt.figure(figsize=(12,5))
    plt.hist(values, bins=num_bins)
    plt.xlabel("{0}Value".format(log_prefix))
    plt.ylabel("Frequency")
    plt.title("{0}\n {1}".format(title, log_prefix))
    plt.tight_layout()
    plt.show()
    
print("Short EDA:")
for ff in sorted(df.columns): #plot a histogram of the numeric data columns
    if (df[ff].dtype == "float64") | (df[ff].dtype == "int64"):
        display_distribution(df[ff], "Feature Distribution of {0}".format(ff))
        
    
plt.figure(figsize=(20,10))
sns.heatmap(df.corr(), annot=True) #correlation matrix
plt.show()
#### End of EDA

X_train, X_test, y_train, y_test = train_test_split(df.iloc[:,:20], df.loc[:,'price'], random_state = 42, test_size = 0.3)

print("Start of model training")
linear_reg = LinearRegression()
scoring = ['neg_mean_squared_error','r2']
scores_linear = cross_validate(linear_reg, X_train, y_train.ravel(),cv=5, scoring=scoring)


lasso_cv = LassoCV(cv=3, random_state=42).fit(X_train, y_train.ravel()) #for optimal alpha parameter
lasso = Lasso(alpha=lasso_cv.alpha_, random_state=42)
scores_lasso = cross_validate(lasso, X_train, y_train.ravel(), scoring=scoring, cv=5)


# hyperparameter tuning of random forest
param_grid = {'bootstrap': [True, False],
              'n_estimators' : [50, 100, 150, 200, 500, 1000],
              'max_depth': [3, 5, 8, 10, 15, 20],
              'max_features': ['auto', 'sqrt'],
              'min_samples_leaf': [1, 2, 4],
              'min_samples_split': [2, 5, 10]}
rf = RandomForestRegressor(random_state=42)
rf_rsv = RandomizedSearchCV(rf, param_grid, cv = 5, random_state= 42, n_jobs= -1)
rf_rsv.fit(X_train, y_train)
scores_forest = cross_validate(rf_rsv.best_estimator_, X_train, y_train, scoring=scoring, cv=5)


print("5 fold cross validated scores on hyperparameter tuned models:")
print(f"Linear Regression \nMSE: {-scores_linear['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_linear['test_r2'].mean().round(3)}")
print(f"Lasso Regression \nMSE: {-scores_lasso['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_lasso['test_r2'].mean().round(3)}")
print(f"RandomForest Regression \nMSE: {-scores_forest['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_forest['test_r2'].mean().round(3)}")

"""b)"""

df['has2ndFlr'] = np.where(df['2ndFlrSF']== 0, 0, 1)
df['Total_Home_Quality'] = df['OverallQual'] + df['OverallCond']
df['Total_Bathrooms'] = (df['FullBath'] + (0.5 * df['HalfBath']))
z = [ row.GrLivArea + row.TotalBsmtSF + row.GarageArea + row.WoodDeckSF + row.OpenPorchSF + row.EnclosedPorch + row['3SsnPorch'] + row.ScreenPorch for index, row in df.iterrows() ]
df['Total_living_SF'] = z
df["SqFtPerRoom"] = round(df["GrLivArea"] / (df["TotRmsAbvGrd"] + df["FullBath"] + df["HalfBath"] + df["BedroomAbvGr"]), 2)
condition = df.loc[:,'OpenPorchSF'] + df.loc[:,'EnclosedPorch'] + df.loc[:,'ScreenPorch'] != 0
df["hasPorch"] = np.where(condition, 1, 0)
df["haswooddeck"] = np.where(df['WoodDeckSF']> 0, 1, 0)
df["hasgarage"] = np.where(df['GarageArea'] <= 0, 0, 1)
df["threeormore_garagespace"] = np.where(df['GarageArea'] >= 704, 1, 0)
df["onecar_garagespace"] = np.where(df['GarageArea'] < 396, 1, 0)
df["twocars_garagespace"] = np.where((df['GarageArea'] >= 396) & (df['GarageArea'] < 704), 1, 0)

df.insert(len(df.columns)-1, 'price', df.pop('price'))

plt.figure(figsize=(20,10))
sns.heatmap(df.corr(), annot=True)

X_train, X_test, y_train, y_test = train_test_split(df.iloc[:,:31], df.loc[:,'price'], random_state = 42, test_size = 0.3)
scaler = StandardScaler().fit(X_train)
#scaler_y = StandardScaler().fit(np.array(y_train)) # not compatible with y_train structure
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)
#y_train_scaled = scaler_y.transform(y_train) 
#y_test_scaled = scaler_y.transform(y_test)

def test_models(X,y):
  scores_linear = cross_validate(linear_reg, X, y,cv=5, scoring=scoring)

  lasso_cv = LassoCV(cv=5, random_state=42).fit(X, y) #for optimal alpha parameter
  lasso = Lasso(alpha=lasso_cv.alpha_, random_state=42)
  scores_lasso = cross_validate(lasso, X, y, scoring=scoring, cv=5)

  rf_rsv = RandomizedSearchCV(rf, param_grid, cv = 5, random_state= 42, n_jobs= -1)
  rf_rsv.fit(X, y)
  scores_forest = cross_validate(rf_rsv.best_estimator_, X, y, scoring=scoring, cv=5)
  print(rf_rsv.best_estimator_.feature_importances_.shape)
  print("5 fold cross validated scores on hyperparameter tuned models:")
  print(f"Linear Regression \nMSE: {-scores_linear['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_linear['test_r2'].mean().round(3)}")
  print(f"Lasso Regression \nMSE: {-scores_lasso['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_lasso['test_r2'].mean().round(3)}")
  print(f"RandomForest Regression \nMSE: {-scores_forest['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_forest['test_r2'].mean().round(3)}")

print("Scores with unscaled X_train:")
test_models(X_train,y_train.ravel())
#print("Scores with unprocessed X_train and scaled y_train:")
#test_models(X_train,y_train_scaled.ravel())
print("Scores with scaled X_train:")
test_models(X_train_scaled,y_train.ravel())
print(rf_rsv.best_estimator_.feature_importances_.shape)

# Scaling X_train improves Lasso Regression (R2 +0.07, MSE +1500000000) but has no effect on Linear Regression and RandomForest Regression.

"""c)"""

rf_rsv = RandomizedSearchCV(rf, param_grid, cv = 5, random_state= 42, n_jobs= -1)
rf_rsv.fit(X_train_scaled, y_train)
importance = rf_rsv.best_estimator_.feature_importances_#np.abs(rf_rsv.best_estimator_.coef_)
feature_names = df.columns[:-1]
print(importance.shape)
print(feature_names.shape)
plt.bar(height=importance, x=feature_names)
plt.title("Feature importances via coefficients")
plt.xticks(rotation=-90)
plt.show()
 
 
 
sfm = SelectFromModel(rf_rsv.best_estimator_, threshold=0.01).fit(X_train_scaled, y_train)
print("Features selected by SelectFromModel: "
      f"{feature_names[sfm.get_support()]}")
#Features selected by SelectFromModel: ['LotArea' 'OverallQual' 'YearBuilt' 'TotalBsmtSF' '1stFlrSF' '2ndFlrSF'
# 'GrLivArea' 'GarageArea' 'WoodDeckSF' 'OpenPorchSF']

# wrapper Method: (takes a long time)
sfs_backward_rf = SequentialFeatureSelector(rf, n_features_to_select=None,
                                         direction='backward').fit(X_train_scaled, y_train.ravel())
print("Features selected by backward sequential selection: "
      f"{feature_names[sfs_backward_rf.get_support()]}")
#Features selected by backward sequential selection: ['OverallQual' 'OverallCond' 'YearBuilt' '1stFlrSF' '2ndFlrSF' 'FullBath'
# 'BedroomAbvGr' 'Fireplaces' 'ScreenPorch']

X_train_backwawrd = sfs_backward_rf.transform(X_train_scaled)
X_train_sfm = sfm.transform(X_train_scaled)
X_test_sfm = sfm.transform(X_test_scaled)
rf_rsv = RandomizedSearchCV(rf, param_grid, cv = 5, random_state= 42, n_jobs= -1)
print("Test on features selected by backward sequential selection: ")
rf_rsv.fit(X_train_backwawrd , y_train.ravel())
scores_forest = cross_validate(rf_rsv.best_estimator_, X_train_backwawrd , y_train.ravel(), scoring=scoring, cv=5)
print(f"RandomForest Regression \nMSE: {-scores_forest['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_forest['test_r2'].mean().round(3)}")
print("Test on features selected by SelectFromModel on our RandomForest Regressor: ")
rf_rsv.fit(X_train_sfm , y_train.ravel())
scores_forest = cross_validate(rf_rsv.best_estimator_, X_train_sfm , y_train.ravel(), scoring=scoring, cv=5)
print(f"RandomForest Regression \nMSE: {-scores_forest['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_forest['test_r2'].mean().round(3)}")

lasso = LassoCV().fit(X_train_scaled, y_train)
importance = np.abs(lasso.coef_)
feature_names = df.columns[:-1]
print(importance.shape)
print(feature_names.shape)
plt.bar(height=importance, x=feature_names)
plt.title("Feature importances via coefficients")
plt.xticks(rotation=-90)
plt.show()



lasso_sfm = SelectFromModel(lasso, threshold=0.01).fit(X_train_scaled, y_train)
print("Features selected by SelectFromModel: "
      f"{feature_names[sfm.get_support()]}")

# wrapper Method: (takes a long time)
sfs_backward_lasso = SequentialFeatureSelector(lasso, n_features_to_select=None,
                                         direction='backward').fit(X_train_scaled, y_train.ravel())
print("Features selected by backward sequential selection: "
      f"{feature_names[sfs_backward_lasso.get_support()]}")
#Features selected by backward sequential selection: ['OverallQual' 'OverallCond' 'YearBuilt' '1stFlrSF' '2ndFlrSF' 'FullBath'
# 'BedroomAbvGr' 'Fireplaces' 'ScreenPorch']

print("Test on features selected by backward sequential selection: ")
X_train_backward = sfs_backward_lasso.transform(X_train_scaled)
lasso_cv = LassoCV(cv=5, random_state=42).fit(X_train_backward, y_train.ravel()) #for optimal alpha parameter
lasso = Lasso(alpha=lasso_cv.alpha_, random_state=42)
scores_lasso = cross_validate(lasso, X_train_backward, y_train.ravel(), scoring=scoring, cv=5)
print(f"Lasso Regression \nMSE: {-scores_lasso['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_lasso['test_r2'].mean().round(3)}")              

print("Test on features selected by SelectFromModel on our Lasso Regressor: ")
X_train_lasso_sfm = lasso_sfm.transform(X_train_scaled)
lasso_cv = LassoCV(cv=5, random_state=42).fit(X_train_lasso_sfm, y_train.ravel()) #for optimal alpha parameter
lasso = Lasso(alpha=lasso_cv.alpha_, random_state=42)
scores_lasso = cross_validate(lasso, X_train_lasso_sfm, y_train.ravel(), scoring=scoring, cv=5)
print(f"Lasso Regression \nMSE: {-scores_lasso['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_lasso['test_r2'].mean().round(3)}")

linear_reg.fit(X_train_scaled, y_train)
importance = np.abs(linear_reg.coef_)
feature_names = df.columns[:-1]
print(importance.shape)
print(feature_names.shape)
plt.bar(height=importance, x=feature_names)
plt.title("Feature importances via coefficients")
plt.xticks(rotation=-90)
plt.show()



linear_sfm = SelectFromModel(linear_reg, threshold=0.01).fit(X_train_scaled, y_train)
print("Features selected by SelectFromModel: "
      f"{feature_names[linear_sfm.get_support()]}")

# wrapper Method: (takes a long time)
sfs_backward_linear = SequentialFeatureSelector(linear_reg, n_features_to_select=None,
                                         direction='backward').fit(X_train_scaled, y_train.ravel())
print("Features selected by backward sequential selection: "
      f"{feature_names[sfs_backward_linear.get_support()]}")

print("Test on features selected by backward sequential selection: ")
X_train_backward = sfs_backward_linear.transform(X_train_scaled)
linear_reg.fit(X_train_backward, y_train)
scores_linear = cross_validate(linear_reg, X_train_backward, y_train,cv=5, scoring=scoring)          
print(f"Linear Regression \nMSE: {-scores_linear['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_linear['test_r2'].mean().round(3)}")
print("Test on features selected by SelectFromModel on our Linear Regressor: ")
X_train_linear_sfm = linear_sfm.transform(X_train_scaled)
linear_reg.fit(X_train_linear_sfm, y_train)
scores_linear = cross_validate(linear_reg, X_train_linear_sfm, y_train,cv=5, scoring=scoring) 
print(f"Linear Regression \nMSE: {-scores_linear['test_neg_mean_squared_error'].mean().round(3)}, R2: {scores_linear['test_r2'].mean().round(3)}")

"""d)"""

X_train_backward = sfs_backward_rf.transform(X_train_scaled)
X_test_backward = sfs_backward_rf.transform(X_test_scaled)
"""d)"""

def evaluate(model, X, y):
    y_pred = model.predict(X)
    try:
        r2 = r2_score(y_pred,y)
    except:
        r2 = None
    mse = mean_squared_error(y_pred,y)
    return r2, mse

def plot_learning_curve(model,X_train_lc,y_train_lc,X_test_lc,y_test_lc):
    r2_train = []
    mse_train = []
    r2_test = []
    mse_test = []
    samples = []
    for i in range(1,len(X_train_lc),5): # very low number of samples is not suitable
        model.fit(X_train_lc[:i],y_train_lc[:i])
        #print(evaluate(model,X_train_lc[:i],y_train_lc[:i]))
        r2_train.append(evaluate(model,X_train_lc[:i],y_train_lc[:i])[0])
        mse_train.append(-evaluate(model,X_train_lc[:i],y_train_lc[:i])[1])
        r2_test.append(evaluate(model,X_test_lc,y_test_lc)[0])
        mse_test.append(-evaluate(model, X_test_lc, y_test_lc)[1])
        samples.append(i)
    print(r2_test)

    plt.plot(samples,r2_test,label='r2 test data')
    plt.plot(samples,r2_train,label='r2 training data')
    axes = plt.gca()
    axes.set_ylim([-0.5, 1.2])
    plt.xlabel("number of training samples")
    plt.ylabel("estimator")
    plt.title("learning curve R2 score")
    plt.legend()
    plt.show()

    plt.plot(samples,mse_test, label='negative mse test data')
    plt.plot(samples,mse_train, label='negative mse training data')
    axes = plt.gca()
    #axes.set_ylim([-0.5, 1.5])
    plt.xlabel("number of training samples")
    plt.ylabel("estimator")
    plt.title("learning curve MSE score")
    plt.legend()
    plt.show()


    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('number of learned training samples')
    ax1.set_ylabel('R2 score', color=color)
    ax1.set_ylim([-0.5, 1.0])
    ax1.plot(samples,r2_test,label='R2 score on test data', color = color)
    ax1.plot(samples,r2_train,label='R2 score on training data',color ='lightsalmon')
    ax1.tick_params(axis='y', labelcolor=color)
    #ax1.legend(loc=3)
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('MSE score', color=color)  # we already handled the x-label with ax1
    ax2.plot(samples,mse_test, label='negative MSE score on test data',color=color)
    ax2.plot(samples,mse_train, label='negative MSE score on training data', color='lightskyblue')
    ax2.tick_params(axis='y', labelcolor=color)
    #https://stackoverflow.com/questions/5484922/secondary-axis-with-twinx-how-to-add-to-legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc=0)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    #plt.legend()
    plt.show()

rf_rsv = RandomizedSearchCV(rf, param_grid, cv = 3, random_state= 42, n_jobs= -1)
rf_rsv.fit(X_train_backward, y_train)
best_rf = rf_rsv.best_estimator_
plot_learning_curve(best_rf,X_train_backward, y_train,X_test_backward,y_test)
