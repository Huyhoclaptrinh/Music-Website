from django.contrib import admin
from .models import UserRegister, UserLibrary, UserHistory, FriendRecommend

# Register your models here.

admin.site.register(UserRegister)
admin.site.register(UserLibrary)
admin.site.register(UserHistory)
admin.site.register(FriendRecommend)