import joblib
from sklearn.ensemble import RandomForestClassifier
import os

model_path = os.path.join(os.path.dirname(__file__), 'model', 'binary_model_1.pkl')
MODEL = joblib.load(model_path)

LABELS = {0: 'Benign', 1: 'Malignant'}

def describe_predict(mass_margin, mass_shape, breast_density):
    features = [[mass_margin, mass_shape, breast_density]]
    prediction = MODEL.predict(features)
    prediction_label = LABELS[prediction[0]]

    return prediction_label
