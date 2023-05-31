from django.contrib import admin
from .models import Music, Post, Comment, PostComment

# Register your models here.
admin.site.register(Music)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostComment)