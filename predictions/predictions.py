import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
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

def predict(image_file):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5],
                             std=[0.5, 0.5, 0.5])
    ])

    image = Image.open(image_file)
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = transform(image).unsqueeze(0)

    # inference
    with torch.no_grad():
        outputs = MODEL(image)
        _, preds = torch.max(outputs, 1)

    return preds.item()
