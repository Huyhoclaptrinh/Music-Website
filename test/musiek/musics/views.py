from django.shortcuts import render

# Create your views here.

def Library(request):
  return render(request,'library.html')