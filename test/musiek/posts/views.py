from django.shortcuts import render

# Create your views here.

def Newsfeed(request):
  return render(request,'newsfeed.html')

def Profile(request):
  return render(request,'profile.html')

def Upload(request):
  return render(request,'upload.html')