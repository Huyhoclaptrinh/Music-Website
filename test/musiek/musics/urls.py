from django.urls import path
from . import views

urlpatterns = [
    path('library/', views.LibraryPage, name='library'),
    path('history/', views.History, name='history'),
    path('library_add/', views.library_add, name='library_add'),
    path('library/<int:library_id>/', views.library_details, name='library_details'),
    path('library/<int:library_id>/delete/', views.delete_library, name='delete_library'),
    path('library/<int:library_id>/remove_song/<int:song_id>/', views.remove_song, name='remove_song'),
]