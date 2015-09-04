"""
@author: John Wittenauer
"""

import os
import sys
import pandas as pd
from datetime import datetime

from sklearn.cluster import *
from sklearn.decomposition import *
from sklearn.ensemble import *
from sklearn.feature_extraction import *
from sklearn.feature_selection import *
from sklearn.linear_model import *
from sklearn.manifold import *
from sklearn.naive_bayes import *
from sklearn.preprocessing import *
from sklearn.svm import *


code_dir = 'C:\\Users\\John\\Documents\\Git\\kaggle\\'
data_dir = 'C:\\Users\\John\\Documents\\Kaggle\\Property Inspection\\'
os.chdir(code_dir)
logger = Logger(data_dir + 'output.txt')
sys.stdout = logger
# sys.stdout = logger.terminal
# logger.close()


def generate_features(data):
    """
    Generates new derived features to add to the data set for model training.
    """
    return data


def process_data(directory, train_file, test_file, label_index, column_offset, ex_generate_features):
    """
    Reads in training data and prepares numpy arrays.
    """
    train_data = load_csv_data(directory, train_file, index='Id')
    test_data = load_csv_data(directory, test_file, index='Id')

    if ex_generate_features:
        train_data = generate_features(train_data)
        test_data = generate_features(test_data)

    X = train_data.iloc[:, column_offset:].values
    y = train_data.iloc[:, label_index].values
    X_test = test_data.values

    # label encode the categorical variables
    for i in range(X.shape[1]):
        if type(X[0, i]) is str:
            le = LabelEncoder()
            le.fit(X[:, i])
            X[:, i] = le.transform(X[:, i])
            X_test[:, i] = le.transform(X_test[:, i])

    print('Data processing complete.')

    return train_data, test_data, X, y, X_test


def define_model(model_type, algorithm):
    """
    Defines and returns a model object of the designated type.
    """
    model = None

    if model_type == 'classification':
        if algorithm == 'bayes':
            model = GaussianNB()
        elif algorithm == 'logistic':
            model = LogisticRegression(penalty='l2', C=1.0)
        elif algorithm == 'svm':
            model = SVC(C=1.0, kernel='rbf', shrinking=True, probability=False, cache_size=200)
        elif algorithm == 'sgd':
            model = SGDClassifier(loss='hinge', penalty='l2', alpha=0.0001, n_iter=1000, shuffle=False, n_jobs=-1)
        elif algorithm == 'forest':
            model = RandomForestClassifier(n_estimators=10, criterion='gini', max_features='auto', max_depth=None,
                                           min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'xt':
            model = ExtraTreesClassifier(n_estimators=10, criterion='gini', max_features='auto', max_depth=None,
                                         min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'boost':
            model = GradientBoostingClassifier(loss='deviance', learning_rate=0.1, n_estimators=100, subsample=1.0,
                                               min_samples_split=2, min_samples_leaf=1, max_depth=3, max_features=None,
                                               max_leaf_nodes=None)
        elif algorithm == 'xgb':
            model = XGBClassifier(max_depth=3, learning_rate=0.1, n_estimators=100, silent=True,
                                  objective='multi:softmax', gamma=0, min_child_weight=1, max_delta_step=0,
                                  subsample=1.0, colsample_bytree=1.0, base_score=0.5, seed=0, missing=None)
        else:
            print('No model defined for ' + algorithm)
            exit()
    else:
        if algorithm == 'ridge':
            model = Ridge(alpha=1.0)
        elif algorithm == 'svm':
            model = SVR(C=1.0, kernel='rbf', shrinking=True, cache_size=200)
        elif algorithm == 'sgd':
            model = SGDRegressor(loss='squared_loss', penalty='l2', alpha=0.0001, n_iter=1000, shuffle=False)
        elif algorithm == 'forest':
            model = RandomForestRegressor(n_estimators=10, criterion='mse', max_features='auto', max_depth=None,
                                          min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'xt':
            model = ExtraTreesRegressor(n_estimators=10, criterion='mse', max_features='auto', max_depth=None,
                                        min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'boost':
            model = GradientBoostingRegressor(loss='ls', learning_rate=0.1, n_estimators=100, subsample=1.0,
                                              min_samples_split=2, min_samples_leaf=1, max_depth=3, max_features=None,
                                              max_leaf_nodes=None)
        elif algorithm == 'xgb':
            # model = XGBRegressor(max_depth=3, learning_rate=0.01, n_estimators=1000, silent=True,
            #                      objective='reg:linear', gamma=0, min_child_weight=1, max_delta_step=0,
            #                      subsample=1.0, colsample_bytree=1.0, base_score=0.5, seed=0, missing=None)
            xg = XGBRegressor(max_depth=7, learning_rate=0.005, n_estimators=1800, silent=True,
                              objective='reg:linear', gamma=0, min_child_weight=1, max_delta_step=0,
                              subsample=0.9, colsample_bytree=0.8, base_score=0.5, seed=0, missing=None)
            model = BaggingRegressor(base_estimator=xg, n_estimators=10, max_samples=1.0, max_features=1.0,
                                     bootstrap=True, bootstrap_features=False)
        else:
            print('No model defined for ' + algorithm)
            exit()

    return model


def bag_of_models():
    """
    Defines the set of models used in the ensemble.
    """
    models = []

    rf1 = RandomForestRegressor(n_estimators=100, criterion='mse', max_features='auto', max_depth=12,
                                min_samples_split=20, min_samples_leaf=10, max_leaf_nodes=None, n_jobs=-1)
    models.append(BaggingRegressor(base_estimator=rf1, n_estimators=10, max_samples=1.0, max_features=1.0,
                                   bootstrap=True, bootstrap_features=False))

    return models


def create_submission(test_data, y_pred, data_dir, submit_file):
    """
    Create a new submission file with test data and predictions generated by the model.
    """
    submit = pd.DataFrame(columns=['Id', 'Hazard'])
    submit['Id'] = test_data.index
    submit['Hazard'] = y_pred
    submit.to_csv(data_dir + submit_file, sep=',', index=False, index_label=False)
    print('Submission file complete.')


def main():
    ex_process_train_data = True
    ex_generate_features = False
    ex_load_model = False
    ex_save_model = False
    ex_visualize_variable_relationships = False
    ex_visualize_feature_distributions = False
    ex_visualize_correlations = False
    ex_visualize_sequential_relationships = False
    ex_visualize_transforms = False
    ex_define_model = True
    ex_train_model = True
    ex_visualize_feature_importance = False
    ex_cross_validate = True
    ex_plot_learning_curve = False
    ex_parameter_search = False
    ex_train_ensemble = False
    ex_create_submission = True

    train_file = 'train.csv'
    test_file = 'test.csv'
    submit_file = 'submission.csv'
    model_file = 'model.pkl'

    model_type = 'regression'  # classification, regression
    algorithm = 'xgb'  # bayes, logistic, ridge, svm, sgd, forest, xt, boost, xgb, nn
    metric = 'gini'  # accuracy, f1, log_loss, mean_absolute_error, mean_squared_error, r2, roc_auc, 'gini'
    ensemble_mode = 'stacking'  # averaging, stacking
    # categories = []
    categories = [3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 16, 19, 21, 27, 28, 29]
    # categories = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18,
    #               19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    early_stopping = False
    label_index = 0
    column_offset = 1
    plot_size = 16
    n_components = 2
    n_folds = 5

    train_data = None
    test_data = None
    X = None
    y = None
    X_test = None
    y_pred = None
    model = None

    all_transforms = [Imputer(missing_values='NaN', strategy='mean', axis=0),
                      LabelEncoder(),
                      OneHotEncoder(n_values='auto', categorical_features=categories, sparse=False),
                      DictVectorizer(sparse=False),
                      FeatureHasher(n_features=1048576, input_type='dict'),
                      VarianceThreshold(threshold=0.0),
                      Binarizer(threshold=0.0),
                      StandardScaler(),
                      MinMaxScaler(),
                      PCA(n_components=None, whiten=False),
                      TruncatedSVD(n_components=None),
                      NMF(n_components=None),
                      FastICA(n_components=None, whiten=True),
                      Isomap(n_components=2),
                      LocallyLinearEmbedding(n_components=2, method='modified'),
                      MDS(n_components=2),
                      TSNE(n_components=2, learning_rate=1000, n_iter=1000),
                      KMeans(n_clusters=8)]

    transforms = [FactorToNumeric(categorical_features=categories, metric='mean'),
                  StandardScaler()]

    print('Starting process (' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ')...')
    print('Model Type = {0}'.format(model_type))
    print('Algorithm = {0}'.format(algorithm))
    print('Scoring Metric = {0}'.format(metric))
    print('Generate Features = {0}'.format(ex_generate_features))
    print('Transforms = {0}'.format(transforms))
    print('Early Stopping = {0}'.format(early_stopping))

    if ex_process_train_data:
        print('Reading in and processing data files...')
        train_data, test_data, X, y, X_test = process_data(data_dir, train_file, test_file, label_index,
                                                           column_offset, ex_generate_features)

    if ex_visualize_variable_relationships:
        print('Visualizing pairwise relationships...')
        # scatter, reg, resid, kde, hex
        visualize_variable_relationships(train_data, 'scatter', ['Hazard', 'T1_V1'])

    if ex_visualize_feature_distributions:
        print('Visualizing feature distributions...')
        # hist, kde
        visualize_feature_distributions(train_data, 'hist', plot_size)

    if ex_visualize_correlations:
        print('Visualizing feature correlations...')
        visualize_correlations(train_data)

    if ex_visualize_sequential_relationships:
        print('Visualizing sequential relationships...')
        visualize_sequential_relationships(train_data, plot_size)

    if ex_visualize_transforms:
        print('Visualizing transformed data...')
        visualize_transforms(X, y, model_type, n_components, transforms)

    if ex_load_model:
        print('Loading model from disk...')
        model = load_model(data_dir + model_file)

    if ex_define_model:
        print('Building model definition...')
        if algorithm == 'nn':
            model = define_nn_model(X, y, transforms)
        else:
            model = define_model(model_type, algorithm)

    if ex_train_model:
        print('Training model...')
        if algorithm == 'nn':
            model, history = train_model(X, y, algorithm, model, metric, transforms, early_stopping)
        else:
            model = train_model(X, y, algorithm, model, metric, transforms, early_stopping)

        if ex_visualize_feature_importance and algorithm in ['forest', 'xt', 'boost']:
            print('Generating feature importance plot...')
            visualize_feature_importance(model.feature_importances_, train_data.columns(), column_offset)

        if ex_cross_validate:
            print('Performing cross-validation...')
            cross_validate(X, y, algorithm, model, metric, transforms, n_folds)

        if ex_plot_learning_curve:
            print('Generating learning curve...')
            plot_learning_curve(X, y, model, metric, transforms, n_folds)

    if ex_save_model:
        print('Saving model to disk...')
        save_model(model, data_dir + model_file)

    if ex_parameter_search:
        print('Performing hyper-parameter grid search...')
        parameter_search(X, y, algorithm, model, metric, transforms, n_folds)

    if ex_train_ensemble:
        print('Creating an ensemble of models...')
        if ensemble_mode == 'averaging':
            y_pred = train_averaged_ensemble(X, y, X_test, metric, transforms, n_folds)
        else:
            y_models, y_true, y_models_test, y_pred = train_stacked_ensemble(X, y, X_test, metric, transforms, n_folds)
            pd.DataFrame(y_models).to_csv(data_dir + 'stacker_train.csv')
            pd.DataFrame(y_true).to_csv(data_dir + 'stacker_label.csv')
            pd.DataFrame(y_models_test).to_csv(data_dir + 'stacker_test.csv')

    if ex_create_submission:
        if not ex_train_ensemble:
            print('Predicting test data...')
            transforms = fit_transforms(X, y, transforms)
            X_test = apply_transforms(X_test, transforms)
            y_pred = model.predict(X_test)

        print('Creating submission file...')
        create_submission(test_data, y_pred, data_dir, submit_file)

    print('Process complete. (' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ')')
    print('')
    print('')
    logger.flush()


if __name__ == "__main__":
    main()
