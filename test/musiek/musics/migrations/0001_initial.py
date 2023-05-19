# Generated by Django 4.2.1 on 2023-05-19 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Music',
            fields=[
                ('music_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('author', models.CharField(max_length=255)),
                ('genre', models.CharField(max_length=255)),
                ('img', models.ImageField(upload_to='static/img')),
                ('total_played', models.IntegerField(default=0)),
                ('total_likes', models.IntegerField(default=0)),
                ('total_comments', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('library_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('music_id', models.ManyToManyField(to='musics.music')),
            ],
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('history_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('music_id', models.ManyToManyField(to='musics.music')),
            ],
        ),
    ]
