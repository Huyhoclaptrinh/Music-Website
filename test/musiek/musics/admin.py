from django.contrib import admin
from .models import Music, Library, History

# Register your models here.
admin.site.register(Music)
admin.site.register(Library)
admin.site.register(History)