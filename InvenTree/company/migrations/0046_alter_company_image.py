# Generated by Django 3.2.13 on 2022-06-27 23:08

import company.models
from django.db import migrations
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0045_alter_company_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='image',
            field=stdimage.models.StdImageField(blank=True, force_min_size=False, null=True, upload_to=company.models.rename_company_image, variations={'preview': (256, 256), 'thumbnail': (128, 128)}, verbose_name='Image'),
        ),
    ]