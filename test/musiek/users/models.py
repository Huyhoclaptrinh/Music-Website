# Create your models here.
from django.db import models


class UserRegister(models.Model):
    user_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )
    fullname = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    dob = models.DateField(auto_now_add=True)
    GENDER_TYPE = (("MALE", "Male"), ("FEMALE", "Female"))
    gender = models.CharField(blank=True, choices=GENDER_TYPE, max_length=10)
    ava = models.ImageField(upload_to="img", default=None)
    wall = models.ImageField(upload_to="img", default=None)

    def __str__(self):
        return self.fullname + " Object"


# class MusicRecommend(models.Model):


class FriendRecommend(models.Model):
    data_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    meta_data = models.TextField()
