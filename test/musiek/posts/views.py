from django.shortcuts import render,redirect
from django.core.files.storage import FileSystemStorage

# Create your views here.

def Newsfeed(request):
  return render(request,'newsfeed.html')

def Profile(request):
  return render(request,'profile.html')

def Upload(request):
  if request.method == "POST":
    upload_file = request.FILES['document']

    fs = FileSystemStorage()
    filename = fs.save(upload_file.name, upload_file)
    uploaded_file_url = fs.url(filename)
    return redirect('upload_detail')

  return render(request,'upload.html')

def UploadDetail(request):
  return render(request,'upload_detail.html')

# def UploadFile(request):
#   return