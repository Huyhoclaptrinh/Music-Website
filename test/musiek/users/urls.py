from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.signIn, name='signin'),
    path('signup/', views.signUp, name='signup'),
    path('auth/', views.signUpAuth, name='auth'),
    path('home/', views.Home, name='home'),
    path('settings/', views.Setting, name='setting'),

    # path('form_submit/', views.form_submit_view, name='form_submit'),
]
