from django.urls import path
from . import views

urlpatterns = [
    path('signin/', views.signIn, name='signin'),
    path('signup/', views.signUp, name='signup'),
    path('auth/', views.signUpAuth, name='auth'),
    path('home', views.Home, name='home'),  # Update the URL pattern name
    path('newsfeed/', views.Newsfeed, name='newsfeed'), 
    path('library/', views.Library, name='library'),
    path('settings/', views.Setting, name='setting'),
    path('profile/', views.Profile, name='profile'),
    path('profile/upload/', views.Upload, name='profile'),
    # path('form_submit/', views.form_submit_view, name='form_submit'),
]
