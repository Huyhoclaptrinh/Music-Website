from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.users, name='users'),
    path('users/library/', views.library, name='library'),
    path('users/newsfeed/', views.newsfeed, name='newsfeed')
]
