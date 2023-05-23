from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import UserRegister

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = UserRegister
        fields = ("username", "email")

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = UserRegister
        fields = ("username", "email")