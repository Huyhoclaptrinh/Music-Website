# Create your models here.
from django.db import models

class userRegister(models.Model):
  user_id = models.IntegerField(null=True)
  fullname = models.CharField(max_length=255)
  username = models.CharField(max_length=255)
  email = models.CharField(max_length=255)
  password = models.CharField(max_length=255)
  dob = models.DateField(null=True)
  GenderType = models.TextChoices("GenderType", "MALE FEMALE")
  gender = models.CharField(blank=True, choices=GenderType.choices, max_length=10)
  ava = models.ImageField(upload_to='static/img',null=True)
  wall = models.ImageField(upload_to='static/img',null=True)

class Music(models.Model):
  music_id = models.IntegerField(null=True)
  name = models.CharField(max_length=255)
  author = models.CharField(max_length=255)
  genre = models.CharField(max_length=255)
  img = models.ImageField(upload_to='static/img',null=True)
  total_played = models.IntegerField(null=True)
  total_likes = models.IntegerField(null=True)
  total_comments = models.IntegerField(null=True)

class Post(models.Model):
  post_id = models.IntegerField(null=True)
  user_id = models.IntegerField(null=True)
  music_id = models.IntegerField(null=True)
  content = models.CharField(max_length=255)
  date = models.DateField(null=True)

class Comment(models.Model):
  comment_id = models.IntegerField(null=True)
  user_id = models.IntegerField(null=True)
  post_id = models.IntegerField(null=True)
  content = models.CharField(max_length=255)
  date = models.DateField(null=True)

class Library(models.Model):
  user_id = models.IntegerField(null=True)
  music_id = models.IntegerField(null=True)

class History(models.Model):
  user_id = models.IntegerField(null=True)
  music_id = models.IntegerField(null=True)
  date = models.DateField(null=True)  

class musicRecommend(models.Model):
  user_id = models.IntegerField(null=True)
  music_id = models.IntegerField(null=True)

class friendRecommend(models.Model):
  user_id_1 = models.IntegerField(null=True)
  user_id_2 = models.IntegerField(null=True)