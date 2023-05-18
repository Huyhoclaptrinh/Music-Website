from django.db import models

# Create your models here.

class Music(models.Model):
  music_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
  name = models.CharField(max_length=255)
  author = models.CharField(max_length=255)
  genre = models.CharField(max_length=255)
  img = models.ImageField(upload_to='static/img')
  total_played = models.IntegerField(default=0)
  total_likes = models.IntegerField(default=0)
  total_comments = models.IntegerField(default=0)

class Library(models.Model):
  library_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
  music_id = models.ManyToManyField(Music)

class History(models.Model):
  history_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
  music_id = models.ManyToManyField(Music)
  date = models.DateField(auto_now_add=True)