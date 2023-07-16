from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserRegister


from .forms import CustomUserCreationForm, CustomUserChangeForm

# Register your models here.
class UserRegisterAdmin(UserAdmin):
    # add_form = CustomUserCreationForm
    # form = CustomUserChangeForm
    # model = UserRegister
    list_display = ['username', 'fullname', 'email','password','gender','birthday','avatar','wall']

# admin.site.register(UserRegister)
# admin.site.register(FriendRecommend)

# Register User admin using the custom admin class
admin.site.register(UserRegister, UserRegisterAdmin)