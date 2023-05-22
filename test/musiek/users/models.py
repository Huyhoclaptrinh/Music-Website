# Create your models here.
from django.db import models

from django.contrib.auth.models import AbstractUser

class UserRegister(AbstractUser):
    user_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )
    fullname = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    dob = models.DateField(auto_now_add=True)
    GENDER_TYPE = (("M", "Male"), ("F", "Female"))
    gender = models.CharField(blank=True, choices=GENDER_TYPE, max_length=10)
    ava = models.ImageField(upload_to="img", default=None)
    wall = models.ImageField(upload_to="img", default=None)

    def __str__(self):
        return self.username + " Object"

# class MusicRecommend(models.Model):

class FriendRecommend(models.Model):
    data_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    meta_data = models.TextField()
