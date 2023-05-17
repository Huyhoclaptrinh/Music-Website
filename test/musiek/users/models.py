# Create your models here.
from django.db import models

class userRegister(models.Model):
  user_id = models.IntegerField()
  fullname = models.CharField(max_length=255)
  username = models.CharField(max_length=255)
  email = models.CharField(max_length=255)
  password = models.CharField(max_length=255)
  dob = models.DateField()
  GenderType = models.TextChoices("GenderType", "MALE FEMALE")
  gender = models.CharField(blank=True, choices=GenderType.choices, max_length=10)
  ava = models.ImageField(upload_to='static/img')
  wall = models.ImageField(upload_to='static/img')

class Music(models.Model):
  music_id = models.IntegerField()
  name = models.CharField(max_length=255)
  author = models.CharField(max_length=255)
  genre = models.CharField(max_length=255)
  img = models.ImageField(upload_to='static/img')
  total_played = models.IntegerField()
  total_likes = models.IntegerField()
  total_comments = models.IntegerField()

class Post(models.Model):
  post_id = models.IntegerField()
  user_id = models.IntegerField()
  music_id = models.IntegerField()
  content = models.CharField(max_length=255)
  date = models.DateField()

class Comment(models.Model):
  comment_id = models.IntegerField()
  user_id = models.IntegerField()
  post_id = models.IntegerField()
  content = models.CharField(max_length=255)
  date = models.DateField()

class Library(models.Model):
  user_id = models.IntegerField()
  music_id = models.IntegerField()

class History(models.Model):
  user_id = models.IntegerField()
  music_id = models.IntegerField()
  date = models.DateField()  

class musicRecommend(models.Model):
  user_id = models.IntegerField()
  music_id = models.IntegerField()

class friendRecommend(models.Model):
  user_id_1 = models.IntegerField()
  user_id_2 = models.IntegerField()