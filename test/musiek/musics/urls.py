from django.urls import path
from . import views

urlpatterns = [
    path('library/', views.Library, name='library'),
    path('history/', views.History, name='history'),
]
