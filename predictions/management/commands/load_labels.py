from django.core.management.base import BaseCommand
from predictions.utils import generate_labels_csv, download_labels_file
from predictions.models import  GroundTruth
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Generate ground truth labels csv file and load them into the database'

    def add_arguments(self, parser):
        parser.add_argument('--benign_dir', type=str, help='Directory containing benign images')
        parser.add_argument('--malignant_dir', type=str, help='Directory containing malignant images')
        parser.add_argument('--file_id', type=str, help='Google drive file id for the CSV')
        parser.add_argument('--download', action='store_true', help='Download the CSV from Google Drive')

    def handle(self, *args, **kwargs):
        benign_dir = kwargs['benign_dir']
        malignant_dir = kwargs['malignant_dir']
        file_id = kwargs['file_id']
        download = kwargs['download']

        output_csv = 'data/ground_truth_labels.csv'

        if download:
            if not file_id:
                self.stderr.write(self.style.ERROR('Please provide a Google Drive file id with --file_id'))
                return
            output_csv = download_labels_file(file_id, output_csv)
        elif benign_dir and malignant_dir:
            output_csv = generate_labels_csv(benign_dir, malignant_dir, output_csv)
        else:
            self.stderr.write(self.style.ERROR('Please provide either --benign_dir and --malignant_dir or use --download with --file_id'))
            return
        
        # load csv into database
        self.stdout.write("Loading labels into the database")
        self.load_labels_to_db(output_csv)

    def load_labels_to_db(self, file_path):
        labels_df = pd.read_csv(file_path)

        # insert into db
        for _, row in labels_df.iterrows():
            GroundTruth.objects.update_or_create(image_id=row['image_id'], label=row['Ground_Truth_Label'])
            
        self.stdout.write(self.style.SUCCESS("Labels loaded successfully"))