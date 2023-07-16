from django.urls import path
from . import views

urlpatterns = [
    path('newsfeed/', views.Newsfeed, name='newsfeed'), 
    path('profile/', views.Profile, name='profile'),
    # path('profile/upload/', views.Upload, name='upload'),
    path('upload/', views.UploadDetail, name='upload_detail'),
    # path('profile/upload_post/', views.upload_post, name='upload_post'),
    # path('', views.UploadFile, name="upload_file"),
    path('get_music/', views.getNewMusic, name="get_music"),
    path('post_comment/', views.post_comment, name='post_comment'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('edit_post/<int:post_id>/', views.edit_post, name='edit_post'),
]
