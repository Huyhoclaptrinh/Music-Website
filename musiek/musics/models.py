from django.db import models
from users.models import UserRegister
from posts.models import Music

# Create your models here.


class Library(models.Model):
    library_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )
    name = models.CharField(max_length=255, null=True)
    music_id = models.ManyToManyField(Music)


class History(models.Model):
    history_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )
    date = models.DateField(auto_now_add=True)


class UserLibrary(models.Model):
    library_id = models.ForeignKey(Library, on_delete=models.CASCADE)
    user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)


class UserHistory(models.Model):
    history_id = models.ForeignKey(History, on_delete=models.CASCADE, null=True)
    user_id = models.OneToOneField(UserRegister, on_delete=models.CASCADE)

class HistoryEntry(models.Model):
    history = models.ForeignKey(History, on_delete=models.CASCADE)
    music = models.ForeignKey(Music, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)