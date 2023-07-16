from django.contrib import admin
from .models import Music, Post, Comment, UserSongInteraction

# Register your models here.
admin.site.register(Music)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(UserSongInteraction)