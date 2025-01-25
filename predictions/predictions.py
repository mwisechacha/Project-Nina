import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
import numpy as np
from PIL import Image
from django.db.models import  Count, Q
from .models import GroundTruth

def load_model():
    model = models.resnet18(pretrained=True)
    num_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_features, 128),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(128, 1),
        nn.Sigmoid()
    )

    model_path = 'predictions/model/trained_model.pth'
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

MODEL = load_model()

LABELS = {0: 'Benign', 1: 'Malignant'}

def predict(image_file):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5],
                             std=[0.5, 0.5, 0.5])
    ])

    image = Image.open(image_file)
    # image = np.array(image)

    # if image.ndim == 2:
    #   image = np.stack([image] * 3, axis=0)
    # elif image.ndim == 3 and image.shape[0] != 3:
    #   image = image[:3, :, :]
    # elif image.ndim != 3:
    #   raise ValueError(f"Invalid image shape: {image.shape}")

    # # convert image to tensor
    # image = torch.tensor(image, dtype=torch.float32)

    # # apply transformations
    # if transform:
    #   image = transform(image).unsqueeze(0)

    if image.mode != 'RGB':
        image = image.convert('RGB')

    image = transform(image).unsqueeze(0)

    # inference
    with torch.no_grad():
        outputs = MODEL(image)
        _, preds = torch.max(outputs, 1)

    prediction_label = LABELS[preds.item()]

    return prediction_label

def get_mammogram_stats():
    benign_count = GroundTruth.objects.filter(model_diagnosis='Benign').count()
    malignant_count = GroundTruth.objects.filter(model_diagnosis='Malignant').count()
    total_count = GroundTruth.objects.all().count()

    return benign_count, malignant_count, total_count

def calculate_metrics():
    true_positives = GroundTruth.objects.filter(Q(model_diagnosis='Malignant') & Q(label=1)).count()
    true_negatives = GroundTruth.objects.filter(Q(model_diagnosis='Benign') & Q(label=0)).count()
    false_positives = GroundTruth.objects.filter(Q(model_diagnosis='Malignant') & Q(label=0)).count()
    false_negatives = GroundTruth.objects.filter(Q(model_diagnosis='Benign') & Q(label=1)).count()

    accuracy = (true_positives + true_negatives) / (true_positives + true_negatives + false_positives + false_negatives)
    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / (true_positives + false_negatives)
    f1_score = 2 * (precision * recall) / (precision + recall)

    return accuracy, precision, recall, f1_score