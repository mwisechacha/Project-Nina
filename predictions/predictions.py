import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
import numpy as np
from PIL import Image

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
