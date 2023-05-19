# Generated by Django 4.2.1 on 2023-05-19 08:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('post_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_file', models.FileField(upload_to='')),
                ('name', models.CharField(max_length=255)),
                ('author', models.CharField(max_length=255)),
                ('genre', models.CharField(max_length=255)),
                ('img', models.ImageField(upload_to='media/img')),
                ('content', models.TextField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('total_played', models.IntegerField(default=0)),
                ('total_likes', models.IntegerField(default=0)),
                ('total_comments', models.IntegerField(default=0)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userregister')),
            ],
        ),
        migrations.CreateModel(
            name='Music',
            fields=[
                ('music_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, related_name='music_info', to='posts.post')),
                ('upload_file', models.FileField(null=True, upload_to='')),
                ('name', models.CharField(max_length=255, null=True)),
                ('author', models.CharField(max_length=255, null=True)),
                ('genre', models.CharField(max_length=255, null=True)),
                ('img', models.ImageField(null=True, upload_to='media/img')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('comment_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=255)),
                ('date', models.DateField(auto_now_add=True)),
                ('post_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.post')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userregister')),
            ],
        ),
    ]
