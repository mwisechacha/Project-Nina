# Generated by Django 5.1.4 on 2025-03-09 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0010_radiologist_mammogram_radiologist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mammogram',
            name='uploaded_at',
            field=models.DateTimeField(),
        ),
    ]
