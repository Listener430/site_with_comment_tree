# Generated by Django 2.2.16 on 2022-02-12 17:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220212_1347'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-parent']},
        ),
    ]
