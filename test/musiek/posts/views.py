from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from .models import Post, Music, Comment, UserSongInteraction
from django.core.files.storage import default_storage
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseNotFound,
    JsonResponse,
)
from django.db.models import F, Case, When
from django.db import models, transaction
from .forms import PostForm
from django.utils import timezone

import os
# Create your views here.

def Newsfeed(request):
    post = Post.objects.all().order_by('-date')
    musics = Music.objects.filter(post__in=post)
    comments = Comment.objects.filter(post__in=post).order_by('-date')
    return render(request, "main_page/newsfeed.html", {'post': post, 'comments':comments, 'musics': musics})

def getNewMusic(request):
    music = Music.objects.first()
    url = music.upload_file.url
    return JsonResponse({"url": url, "status": True})

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
        recent_posts = Post.objects.filter(user_id=request.user).order_by('-date')
        
        return render(request, "main_page/profile.html", {'recent_posts': recent_posts, 'username': username})
    
    else:
        # Render the upload form template
        return render(request, 'main_page/upload_detail.html')
    
    # return render(request, "upload_detail.html")

def Profile(request):
    recent_posts = Post.objects.filter(user_id=request.user).order_by('-date')
    musics = Music.objects.filter(post__in=recent_posts)
    comments = Comment.objects.filter(post__in=recent_posts).order_by('-date')
    return render(request, "main_page/profile.html", {'recent_posts': recent_posts, 'comments':comments, 'musics':musics })

def post_comment(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        post_id = request.POST.get('post_id')
        user = request.user
        page = request.POST.get('page')

        try:
            post = Post.objects.get(post_id=post_id)
        except Post.DoesNotExist:
            # Handle the case where the Post does not exist
            return HttpResponse("Invalid post_id")

        # Create and save the comment
        comment = Comment.objects.create(user_id=user, post=post, content=content)

        post.total_comments = post.get_total_comments()
        post.save()

        # Determine the redirect URL based on the page value
        if page == 'profile':
            return redirect('profile')
        elif page == 'newsfeed':
            return redirect('newsfeed')

    return redirect('newsfeed')

def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, comment_id=comment_id)
    page = request.POST.get('page')
    if comment.user_id == request.user:
        post = comment.post

        comment.delete()

        post.total_comments = post.get_total_comments()
        post.save()

    if page == 'profile':
        return redirect('profile')
    elif page == 'newsfeed':
        return redirect('newsfeed')
    else:
        return redirect('newsfeed')
    
def delete_post(request, post_id):
    post = get_object_or_404(Post, post_id=post_id)
    if post.user_id == request.user:
        post.delete()
    return redirect('profile')

def edit_post(request, post_id):
    post = get_object_or_404(Post, post_id=post_id)

    if request.method == 'POST':
        edit_form = PostForm(request.POST, instance=post)
        if edit_form.is_valid():
            edit_form.save()  # Save the edited post

            return redirect('profile')  # Redirect to the profile page after editing the post
    else:
        edit_form = PostForm(instance=post)

    return render(request, 'main_page/profile.html', {'edit_form': edit_form})

def like_song(request, music_id):
    if request.method == 'POST':
        music = Music.objects.get(music_id=music_id)
        user = request.user
        
        # Check if a UserSongInteraction instance exists for this user and song
        interaction, created = UserSongInteraction.objects.get_or_create(user=user, music=music)

        # Update the likes field
        if created or not interaction.likes:
        # If the interaction is created for the first time or the previous state was not liked,
        # update the likes field and increase the total_likes count
            interaction.likes = True
            interaction.save()

            # Update the Post model's total_likes field
            post = music.post
            post.total_likes += 1
            post.save()
        else:
            # If the interaction already existed and the previous state was liked,
            # remove the like and decrease the total_likes count
            interaction.likes = False
            interaction.save()

            # Update the Post model's total_likes field
            post = music.post
            post.total_likes -= 1
            post.save()

        return redirect('home')

# def UploadFile(request):
#   return
