# Generated by Django 4.2.1 on 2023-05-31 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('musics', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historyentry',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
