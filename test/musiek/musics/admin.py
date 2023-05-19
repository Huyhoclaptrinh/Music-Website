from django.contrib import admin
from .models import Library, History, UserLibrary, UserHistory
# Register your models here.
admin.site.register(Library)
admin.site.register(History)
admin.site.register(UserLibrary)
admin.site.register(UserHistory)
