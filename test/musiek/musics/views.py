from django.shortcuts import render, redirect, get_object_or_404
from .models import UserHistory, Music, UserLibrary, Library, History
from .forms import AddSongForm
import datetime
from django.http import HttpResponse
import json
from django.utils import timezone
from django.http import JsonResponse
# Create your views here.


def LibraryPage(request):
    libraries = Library.objects.all()
    return render(request, "main_page/library.html", {'libraries': libraries})


def historyShow(request):
    user = request.user
    user_history = UserHistory.objects.filter(user_id__exact=user)
    selected_date = request.GET.get(
        "selected_date"
    )  # Get the selected date from the request

    if selected_date:
        selected_datetime = datetime.datetime.strptime(selected_date, "%m/%d/%Y %I:%M %p")
        selected_date = selected_datetime.strftime("%Y-%m-%d")
        user_history = user_history.filter(history_id__date=selected_date)
    return render(
        request,
        "main_page/history.html",
        {"user_history": user_history, "selected_date": selected_date},
    )

def library_add(request):
    songs = Music.objects.all()
    if request.method == 'POST':
        selected_songs = request.POST.getlist('selected_songs')
        library_name = request.POST.get('library_name')
        library = Library.objects.create(name=library_name)
        for song_id in selected_songs:
            song = Music.objects.get(music_id=song_id)
            library.music_id.add(song)
        user_library = UserLibrary.objects.create(library_id=library, user_id=request.user)
        # Save the instances
        library.save()
        user_library.save()
        return redirect('library')  # Redirect to a confirmation page
    return render(request, 'main_page/library_add.html', {'songs': songs})

def library_details(request, library_id):
    user_library = get_object_or_404(UserLibrary, library_id=library_id)

    # Check if the logged-in user is the creator of the library
    is_creator = user_library.user_id == request.user

    library = user_library.library_id

    # Handle form submission for adding songs
    if request.method == 'POST':
        form = AddSongForm(request.POST)

        if form.is_valid() and is_creator:
            selected_songs = form.cleaned_data['selected_songs']

            # Add the selected songs to the library
            library.music_id.add(*selected_songs)

            return redirect('library_details', library_id=library_id)
    else:
        form = AddSongForm()

    return render(request, "main_page/library_details.html", {'user_library': user_library, 'library': library, 'is_creator': is_creator, 'form': form})

def delete_library(request, library_id):
    library = Library.objects.get(library_id=library_id)
    library.delete()
    return redirect('library')

def remove_song(request, library_id, song_id):
    # Retrieve the UserLibrary object based on library_id
    user_library = get_object_or_404(UserLibrary, library_id=library_id)

    # Check if the logged-in user is the creator of the library
    if user_library.user_id != request.user:
        return redirect('library_details', library_id=library_id)

    # Retrieve the Music object based on song_id
    music = get_object_or_404(Music, music_id=song_id)

    # Remove the Music object from the library
    user_library.library_id.music_id.remove(music)

    return redirect('library_details', library_id=library_id)

def search_results(request):
    query = request.GET.get('search_query')

    # Query the Music model to retrieve matching songs
    songs = Music.objects.filter(name__icontains=query)

    context = {
        'songs': songs,
        'query': query
    }

    return render(request, 'main_page/search_results.html', context)

def save_to_history(request, music_id):
    if request.method == 'POST':
        user = request.user
        music = Music.objects.get(music_id=music_id)

        user_history, _ = UserHistory.objects.get_or_create(user_id=user)

        history = user_history.history_id
        if history is None:
            # Create a new history entry and add the music
            history = History.objects.create(date=timezone.now())
            history.music_id.add(music)
            user_history.history_id = history
            user_history.save()
        else:
            if music in history.music_id.all():
                # Update the timestamp of the existing history entry
                history.date = timezone.now()
                history.save()
            else:
                # Add the music to the existing history entry
                history.music_id.add(music)

        response_data = {'message': 'Music saved to history successfully'}
        return JsonResponse(response_data)
        
    else:
        response_data = {'message': 'Invalid request method'}
        return JsonResponse(response_data)