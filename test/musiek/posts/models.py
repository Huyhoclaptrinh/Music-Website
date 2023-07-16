from django.db import models
from users.models import UserRegister
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Post(models.Model):
    post_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )
    user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    upload_file = models.FileField(upload_to="audio")
    name = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    img = models.ImageField(upload_to="img")
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    total_played = models.IntegerField(default=0)
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)

    def __str__(self):
        return self.user_id.username + " posts " + self.name
    
    def get_total_comments(self):
        comment_count = Comment.objects.filter(post=self).count()
        return comment_count

    def clean(self):
        super().clean()
        if self.upload_file:
            if not self.upload_file.name.endswith(".mp3"):
                raise ValidationError("Only .mp3 files are allowed for upload.")

    def save(self, *args, **kwargs):
        created = not self.pk
        self.total_comments = self.get_total_comments()
        super().save(*args, **kwargs)
        if created:
            Music.objects.create(
                post=self,
                upload_file=self.upload_file,
                name=self.name,
                author=self.author,
                genre=self.genre,
                img=self.img,
            )
        else:
            music_instance, _ = Music.objects.get_or_create(post=self)
            if music_instance:
                music_instance.upload_file = self.upload_file
                music_instance.name = self.name
                music_instance.author = self.author
                music_instance.genre = self.genre
                music_instance.img = self.img
                music_instance.total_played = self.total_played
                music_instance.total_likes = self.total_likes
                music_instance.save()

    def delete(self, *args, **kwargs):
        if self.upload_file:
            # Delete audio file
            audio_path = str(self.upload_file)
            if default_storage.exists(audio_path):
                default_storage.delete(audio_path)
        if self.img:
            # Delete img file
            img_path = str(self.img)
            if default_storage.exists(img_path):
                default_storage.delete(img_path)
        # Call the superclass delete() method
        super().delete(*args, **kwargs)

class Comment(models.Model):
    comment_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )
    user_id = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    content = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_id.username + " comment on " + self.post.name

class Music(models.Model):
    music_id = models.BigAutoField(
        auto_created=True, serialize=False, primary_key=True, verbose_name="ID"
    )
    post = models.ForeignKey(
        "Post",
        on_delete=models.CASCADE,
        related_name="music_info",
        null=True,
        blank=True,
    )
    upload_file = models.FileField(null=True, upload_to="audio")
    name = models.CharField(max_length=255, null=True)
    author = models.CharField(max_length=255, null=True)
    genre = models.CharField(max_length=255, null=True)
    img = models.ImageField(upload_to="img", null=True)
    total_played = models.IntegerField(default=0)
    total_likes = models.IntegerField(default=0)
    # total_comments = models.IntegerField(default=0)

    # def clean(self):
    #     if not self.post:
    #         raise ValidationError("A Music instance must be associated with a Post.")

    def save(self, *args, **kwargs):
        # is_post_update = False
        # if "force_post_update" in kwargs:
        #     is_post_update = kwargs.pop("force_post_update")
        # if self.pk and not is_post_update:
        #     raise ValidationError(
        #         "Editing the Music instance directly is not allowed. Please edit the associated Post."
        #     )
        # else:
        super().save(*args, **kwargs)

    # def delete(self, using=None, keep_parents=False):
    #     if self.post is None:
    #         super().delete(using, keep_parents)
    #     else:
    #         raise ValidationError(
    #             "Cannot delete the Music instance while the corresponding Post still exists."
    #         )
        
    def __str__(self):
        return self.name + " by " + self.author

class UserSongInteraction(models.Model):
    user = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    music = models.ForeignKey(Music, on_delete=models.CASCADE)
    listens = models.PositiveIntegerField(default=0)
    likes = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + " interact with " + self.music.name + " by " + self.music.author
    
@receiver(post_delete, sender=Music)
def delete_music_files(sender, instance, **kwargs):
# Delete the associated audio file
    if instance.upload_file:
        instance.upload_file.delete(save=False)
    # Delete the associated image file
    if instance.img:
        instance.img.delete(save=False)

class UserSongInteraction(models.Model):
    user = models.ForeignKey(UserRegister, on_delete=models.CASCADE)
    music = models.ForeignKey(Music, on_delete=models.CASCADE)
    listens = models.PositiveIntegerField(default=0)
    likes = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + " interact with " + self.music.name + " by " + self.music.author



