from django.contrib import admin
from .models import UserRegister, FriendRecommend

# Register your models here.

admin.site.register(UserRegister)
admin.site.register(FriendRecommend)