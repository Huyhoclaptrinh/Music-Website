# Generated by Django 4.2.1 on 2023-05-24 02:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('musics', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='library',
            name='name',
            field=models.CharField(max_length=255, null=True),
        ),
    ]