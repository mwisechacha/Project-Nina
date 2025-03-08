import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models import ResNet18_Weights
from torchvision import transforms
import numpy as np
import cv2
from PIL import Image
from django.db.models import  Count, Q
from .models import GroundTruth

# def preprocess_ploaded_image(image_path):
#     image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
#     image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)

def load_model():
    weights = ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)
    num_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_features, 128),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(128, 1),
    )

    model_path = 'predictions/model/trained_model_3.pth'
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
    model.eval()
    return model

MODEL = load_model()

LABELS = {0: 'Benign', 1: 'Malignant'}

def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)

    if image.ndim == 2:
        image = np.stack([image] * 3, axis=2)

    print(f"Image shape before conversion to PIL: {image.shape}")

    image = Image.fromarray(image.astype(np.uint8))

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5],
                             std=[0.5, 0.5, 0.5])
    ])

    image = transform(image).unsqueeze(0)
    return image

def predict(image_file):
    image = preprocess_image(image_file)

    print(image.shape)

    # inference
    with torch.no_grad():
        outputs = MODEL(image)
        outputs = torch.sigmoid(outputs)
        preds = (outputs > 0.5).int()

    print(f"Model raw output: {outputs.item()}")
    print(f"Predicted class (0=Benign, 1=Malignant): {preds.item()}")

    prediction_label = LABELS[preds.item()]

    return prediction_label

def get_mammogram_stats():
    benign_count = GroundTruth.objects.filter(label=0).count()
    malignant_count = GroundTruth.objects.filter(label=1).count()
    total_count = GroundTruth.objects.all().count()

    return benign_count, malignant_count, total_count

