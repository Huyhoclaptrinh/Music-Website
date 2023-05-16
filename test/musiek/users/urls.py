from django.urls import path
from . import views

urlpatterns = [
    path('', views.signIn, name='signin'),
    path('signup/', views.signUp, name='signup'),
    path('auth/', views.signUpAuth, name='auth'),
    path('home/', views.Home, name='home'),
    path('newsfeed/', views.Newsfeed, name='newsfeed'), 
    path('library/', views.Library, name='library'),
    path('settings/', views.Setting, name='setting'),
    path('profile/', views.Profile, name='profile'),
    path('profile/upload/', views.Upload, name='upload'),
    # path('form_submit/', views.form_submit_view, name='form_submit'),
]
