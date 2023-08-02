from django.contrib import admin
from django.http.request import HttpRequest
from .models import Music, Post, Comment, UserSongInteraction

class MusicAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

# Register your models here.
admin.site.register(Music, MusicAdmin)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(UserSongInteraction)