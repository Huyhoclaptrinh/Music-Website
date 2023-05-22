from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserRegister, FriendRecommend

# Register your models here.
class UserRegisterAdmin(UserAdmin):
    list_display = ['username', 'fullname', 'email']

# admin.site.register(UserRegister)
admin.site.register(FriendRecommend)

# Register User admin using the custom admin class
admin.site.register(UserRegister, UserRegisterAdmin)