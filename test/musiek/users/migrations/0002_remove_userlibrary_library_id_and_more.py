# Generated by Django 4.2.1 on 2023-05-18 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userlibrary',
            name='library_id',
        ),
        migrations.RemoveField(
            model_name='userlibrary',
            name='user_id',
        ),
        migrations.DeleteModel(
            name='UserHistory',
        ),
        migrations.DeleteModel(
            name='UserLibrary',
        ),
    ]
