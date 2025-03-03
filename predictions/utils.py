import gdown
import os
import csv
from predictions.models import ModelMetrics
from django.http import JsonResponse

def download_labels_file(file_id, dest_path):
    url = f'https://drive.google.com/uc?id={file_id}'
    print("Downloading ground truth labels from google drive")
    gdown.download(url, output=dest_path, quiet=False)
    print(f"Labels downloaded at {dest_path}")
    return dest_path

def generate_labels_csv(benign_dir, malignant_dir, output_csv):
    benign_files = [os.path.join(benign_dir, f) for f in os.listdir(benign_dir) if f.endswith('.npy')]
    malignant_files = [os.path.join(malignant_dir, f) for f in os.listdir(malignant_dir) if f.endswith('.npy')]

    # a list of files and labels in pairs
    data = [(f, 0) for f in benign_files] + [(f, 1) for f in malignant_files]

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['image_id', 'Ground_Truth_Label'])
        writer.writerows(data)

    print(f"labels csv generated at {output_csv}")
    return output_csv

def get_conf_matrix_data(request):
    metrics = ModelMetrics.objects.filter(target=0)

    confusion_matrices = {}

    model_sample_sizes = {
        "ResNet18": 2972,
        "Random Forest Classifier": 962,
        "Random Forest CLf-Birads": 962
    }

    for metric in metrics:
        model_name = metric.model_name
        total_samples = model_sample_sizes.get(model_name, None)

        if total_samples is None:
            continue  

        try:
            TP = (metric.precision / 100) * (metric.recall / 100) * total_samples
            FN = (metric.recall / 100) * total_samples - TP
            FP = (metric.precision / 100) * total_samples - TP
            TN = total_samples - (TP + FN + FP)

            # Ensure all values are non-negative integers
            TP, FP, FN, TN = max(0, int(TP)), max(0, int(FP)), max(0, int(FN)), max(0, int(TN))

        except ZeroDivisionError:
            TP, FP, FN, TN = 0, 0, 0, 0  

        confusion_matrices[model_name] = {
            "labels": ["Benign", "Malignant"],
            "matrix": [
                [TP, FN], 
                [FP, TN]  
            ]
        }

    return JsonResponse(confusion_matrices)