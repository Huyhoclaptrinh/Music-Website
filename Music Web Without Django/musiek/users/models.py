from django.db import models

# Create your models here.
class signUp(models.Model):
    name = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)