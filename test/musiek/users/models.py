from django.db import models

# Create your models here.
from django.db import models

class userRegister(models.Model):
  fullname = models.CharField(max_length=255)
  username = models.CharField(max_length=255)
  email = models.CharField(max_length=255)
  password = models.CharField(max_length=255)