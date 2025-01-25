import gdown
import os
import csv

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