from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import Post, Music
import json

# Create your views here.


def Newsfeed(request):
    data = Music.objects.all()  # Retrieve all instances of the model
    return render(request, "newsfeed.html", {'data': data})


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
        recent_posts = Post.objects.filter(user_id=request.user).order_by('-date')[:5].values()
        if recent_posts is not None:
            response = redirect('profile')

            response.set_cookie('recent_posts', json.dumps(recent_posts))
            return response
    
    return render(request, "upload_detail.html")

def Profile(request):
    recent_posts = request.COOKIES.get('recent_posts')
    recent_posts = json.loads(recent_posts)
    response = render(request, "profile.html", {'recent_posts': recent_posts})
    response.delete_cookie('recent_posts')
    return response

# def UploadFile(request):
#   return
