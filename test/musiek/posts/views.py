from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import Post

# Create your views here.


def Newsfeed(request):
    return render(request, "newsfeed.html")


# def Profile(request):
#     return render(request, "profile.html")


# def Upload(request):
#     return render(request, "upload.html")


def UploadDetail(request):
    if request.method == 'POST':
        upload_file = request.FILES.get('upload_file')
        name = request.POST.get('name')
        author = request.POST.get('author')
        genre = request.POST.get('genre')
        img = request.FILES.get('img')
        content = request.POST.get('content')

        post = Post(
            user_id = request.user,
            upload_file=upload_file,
            name=name,
            author=author,
            genre=genre,
            img=img,
            content=content
        )
        post.save()
        recent_posts = Post.objects.order_by('-date')[:5]  # Get the latest 5 posts, adjust as needed

        return render(request, 'profile.html', {'recent_posts': recent_posts})
    
    return render(request, "upload_detail.html")

def Profile(request):
    return render(request, 'profile.html')

# def UploadFile(request):
#   return
