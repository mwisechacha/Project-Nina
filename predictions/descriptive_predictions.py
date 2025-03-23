import joblib
import os
import pandas as pd

from predictions.predictions import predict

model_path = os.path.join(os.path.dirname(__file__), 'model', 'binary_model_1.pkl')
MODEL_1 = joblib.load(model_path)

pipeline_path = os.path.join(os.path.dirname(__file__), 'pipeline', 'binary_pipeline_1.pkl')
PIPELINE_1 = joblib.load(pipeline_path)

LABELS_1 = {0: 'BENIGN', 1: 'MALIGNANT'}
COLUMN_NAMES = ['mass_margin', 'mass_shape', 'breast_density']
BREAST_DENSITY_MAPPING = {
    'category_a': 1,
    'category_b': 2,
    'category_c': 3,
    'category_d': 4
}

MODEL_2 = joblib.load(os.path.join(os.path.dirname(__file__), 'model', 'BIRADS_model.pkl'))
PIPELINE_2 = joblib.load(os.path.join(os.path.dirname(__file__), 'pipeline', 'binary_pipeline_2.pkl'))
# print(PIPELINE_2.named_steps['preprocessor'].transformers_[0][1].categories_)
LABELS_2 = {0: 'Incomplete',
            1: 'Negative',
            2: 'Benign',
            3: 'Probably benign',
            4: 'Suspicious of malignacy',
            5: 'Highly suggestive of malignancy'}

RECOMMENDATIONS = {
    0: 'Need additional imaging to further evaluate',
    1: 'Continue routine annual screening',
    2: 'Continure routine annual screening',
    3: 'Short term follow-up is suggested (6 months)',
    4: 'Biopsy should be considered',
    5: 'Biopsy is required'
}


def describe_predict(mass_margin, mass_shape, breast_density, image_path):
    # check for missing values
    if mass_margin is None or mass_shape is None or breast_density is None or image_path is None:
        raise ValueError("Missing values")
    
    # map breast density
    breast_density = BREAST_DENSITY_MAPPING[breast_density]
    
    features = [[mass_margin, mass_shape, breast_density]]

    try:
        pathology_prediction_label = predict(image_path)
        print(f"ResNet Model prediction: {pathology_prediction_label}")

        pathology_mapping = {
            'Benign': 'BENIGN',
            'Malignant': 'MALIGNANT'
        }

        pathology_prediction_label = pathology_mapping[pathology_prediction_label]
        if pathology_prediction_label is None:
            raise ValueError(f"Unexpected pathology label: {pathology_prediction_label}")
        
    except Exception as e:
        raise RuntimeError(f"ResNet Model prediction failed: {e}")

    # model 1: predict pathology
    try:
        features_df = pd.DataFrame(features, columns=COLUMN_NAMES)

        # pass df through the pipeline
        prepared_features = PIPELINE_1.transform(features_df)

        # make prediction from model_1
        prediction = MODEL_1.predict(prepared_features)
        print(prediction[0])
        prediction_label = LABELS_1[prediction[0]]

        print(f"Model 1 prediction: {prediction_label}")

    except Exception as e:
        raise RuntimeError(f"Model 1 prediction failed: {e}")

    # model 2: predict BI-RADS
    try:
        features_2 = [[mass_margin, mass_shape, breast_density, pathology_prediction_label]]
        features_df_2 = pd.DataFrame(features_2, columns=COLUMN_NAMES + ['pathology'])

        if features_df_2.isnull().values.any():
            raise ValueError("Model 2 received invalid input values.")

        if 'pathology' not in PIPELINE_2.feature_names_in_:
            raise ValueError("Pipeline 2 does not expect 'pathology' feature.")

        prepared_features_2 = PIPELINE_2.transform(features_df_2)
        prediction_2 = MODEL_2.predict(prepared_features_2)
        predicted_class = int(prediction_2[0])
        prediction_label_2 = LABELS_2[predicted_class]


        print(f"Model 2 prediction: {prediction_label_2}")

        probability_mapping = {
            0: 0,
            1: 0,
            2: 0,
            3: 2,
            4: 50,
            5: 95,
        }

        probability_of_cancer = probability_mapping[predicted_class]
        recommendation = RECOMMENDATIONS[predicted_class]

    except Exception as e:
        raise RuntimeError(f"Model 2 prediction failed: {e}")

    return pathology_prediction_label, prediction_label_2, probability_of_cancer, recommendation
