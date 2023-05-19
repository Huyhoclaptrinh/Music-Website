from django.urls import path
from . import views

urlpatterns = [
    path('newsfeed/', views.Newsfeed, name='newsfeed'), 
    path('profile/', views.Profile, name='profile'),
    path('profile/upload/', views.Upload, name='upload'),
    path('upload/detail/', views.UploadDetail, name='upload_detail'),
    # path('', views.UploadFile, name="upload_file"),
]
