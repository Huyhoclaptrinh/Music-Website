from django.shortcuts import render

# Create your views here.

def Library(request):
  return render(request, 'main_page/library.html')

def History(request):
  return render(request, 'main_page/history.html')