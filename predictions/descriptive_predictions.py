import joblib
from sklearn.ensemble import RandomForestClassifier
import os
import pandas as pd

model_path = os.path.join(os.path.dirname(__file__), 'model', 'binary_model_1.pkl')
MODEL = joblib.load(model_path)

pipeline_path = os.path.join(os.path.dirname(__file__), 'pipeline', 'binary_pipeline_1.pkl')
PIPELINE = joblib.load(pipeline_path)

LABELS = {0: 'Benign', 1: 'Malignant'}
COLUMN_NAMES = ['mass_margin', 'mass_shape', 'breast_density']
BREAST_DENSITY_MAPPING = {
    'category_a': 1,
    'category_b': 2,
    'category_c': 3,
    'category_d': 4
}


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
    prepared_features = PIPELINE.transform(features_df)

    # make prediction
    prediction = MODEL.predict(prepared_features)
    prediction_label = LABELS[prediction[0]]


    return prediction_label
