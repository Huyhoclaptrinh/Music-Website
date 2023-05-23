from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import Post, Music
# Create your views here.


def Newsfeed(request):
    data = Music.objects.all()  # Retrieve all instances of the model
    return render(request, "main_page/newsfeed.html", {'data': data})


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
            user_id=request.user,
            upload_file=upload_file,
            name=name,
            author=author,
            genre=genre,
            img=img,
            content=content
        )
        post.save()
        
        # Access the ID of the saved post
        post_id = post.post_id
        
        # Retrieve the post and access the associated userRegister model
        post = Post.objects.get(post_id=post_id)
        username = post.user_id.username  # Access the username attribute
        recent_posts = Post.objects.filter(user_id=request.user).order_by('-date')[:5]
        
        return render(request, "main_page/profile.html", {'recent_posts': recent_posts, 'username': username})
    
    else:
        # Render the upload form template
        return render(request, 'main_page/upload_detail.html')
    
    # return render(request, "upload_detail.html")

def Profile(request):
    recent_posts = Post.objects.filter(user_id=request.user).order_by('-date')[:5]
    post = Post.objects.get(Post.post_id)
    username = post.user_id.username
    return render(request, "main_page/profile.html", {'recent_posts': recent_posts, 'username': username})

# def UploadFile(request):
#   return
