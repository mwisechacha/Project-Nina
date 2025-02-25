import joblib
from sklearn.ensemble import RandomForestClassifier
import os
import pandas as pd

model_path = os.path.join(os.path.dirname(__file__), 'model', 'binary_model_1.pkl')
MODEL_1 = joblib.load(model_path)

pipeline_path = os.path.join(os.path.dirname(__file__), 'pipeline', 'binary_pipeline_1.pkl')
PIPELINE_1 = joblib.load(pipeline_path)

LABELS_1 = {0: 'Benign', 1: 'Malignant'}
COLUMN_NAMES = ['mass_margin', 'mass_shape', 'breast_density']
BREAST_DENSITY_MAPPING = {
    'category_a': 1,
    'category_b': 2,
    'category_c': 3,
    'category_d': 4
}

MODEL_2 = joblib.load(os.path.join(os.path.dirname(__file__), 'model', 'binary_model_2.pkl'))
PIPELINE_2 = joblib.load(os.path.join(os.path.dirname(__file__), 'pipeline', 'binary_pipeline_2.pkl'))
LABELS_2 = {0: 'need additional imaging',
            1: 'negative',
            2: 'benign',
            3: 'probably benign',
            4: 'suspicious',
            5: 'highly suggestive of malignancy'}


def describe_predict(mass_margin, mass_shape, breast_density):
    # check for missing values
    if mass_margin is None or mass_shape is None or breast_density is None:
        raise ValueError("Missing values")
    
    # map breast density
    breast_density = BREAST_DENSITY_MAPPING[breast_density]
    
    features = [[mass_margin, mass_shape, breast_density]]

    # create df
    features_df = pd.DataFrame(features, columns=COLUMN_NAMES)

    # pass df through the pipeline
    prepared_features = PIPELINE_1.transform(features_df)

    # make prediction from model_1
    prediction = MODEL_1.predict(prepared_features)
    prediction_label = LABELS_1[prediction[0]]

    features_2 = [[mass_margin, mass_shape, breast_density, prediction[0]]]
    features_df_2 = pd.DataFrame(features_2, columns=COLUMN_NAMES + ['pathology'])
    prepared_features_2 = PIPELINE_2.transform(features_df_2)

    print("Features for MODEL_2:")
    # print(features_df_2)
    # print(features_df_2.dtypes)

    # features_df_2 = features_df_2.astype({
    #     'mass_margin': 'float64',
    #     'mass_shape': 'float64',
    #     'breast_density': 'float64',
    #     'pathology': 'float64'
    # })

    # # Debugging: Print the DataFrame after type conversion
    # print("Features for MODEL_2 after type conversion:")
    # print(features_df_2)
    # print(features_df_2.dtypes)

    prediction_2 = MODEL_2.predict(prepared_features_2)
    prediction_label_2 = LABELS_2[prediction_2[0]]

    return prediction_label, prediction_label_2
