from django.db import models
from users.models import UserRegister
from musics.models import Music

# Create your models here.

class Post(models.Model):
  post_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
  user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
  music_id = models.OneToOneField(Music, on_delete=models.CASCADE)
  content = models.CharField(max_length=255)
  date = models.DateField(auto_now_add=True)

class Comment(models.Model):
  comment_id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
  user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
  post_id = models.ForeignKey(Post, on_delete=models.CASCADE)
  content = models.CharField(max_length=255)
  date = models.DateField(auto_now_add=True)