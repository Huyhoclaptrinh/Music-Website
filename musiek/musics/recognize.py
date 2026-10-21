from scipy import signal
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import soundfile as sf
import os
from django.conf import settings
import librosa
import numpy as np
from .models import Music

# Preprocess the audio file and save the features as a numpy array
def preprocess_audio(audio_file, filter_order=4, cutoff_freq=1000):
    # Load the audio file
    audio_data, sample_rate = librosa.load(audio_file)

    # Apply signal filtering
    b, a = signal.butter(filter_order, cutoff_freq, fs=sample_rate, btype='low')
    audio_data = signal.lfilter(b, a, audio_data)

    # Extract MFCC features
    mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=40)

    return mfccs

def find_closest_song(unknown_song, database_songs, filenames):
    # Reshape the unknown_song to match the number of features in database_songs
    unknown_song = unknown_song.reshape(1, -1)

    # Perform clustering using K-means
    n_clusters = 2  # Number of clusters
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(database_songs)

    # Predict the cluster for the unknown song
    unknown_cluster = kmeans.predict(unknown_song)

    # Find the closest song in the same cluster as the unknown song
    cluster_indices = np.where(kmeans.labels_ == unknown_cluster)[0]  # Extract the array from the tuple
    cluster_songs = [database_songs[i] for i in cluster_indices]
    cluster_filenames = [filenames[i] for i in cluster_indices]

    # Check if there are any songs in the same cluster as the unknown song
    if len(cluster_songs) > 0:
        # Find the closest song index and filename
        closest_song_index = np.argmin(np.linalg.norm(cluster_songs - unknown_song, axis=1))
        closest_song_filename = cluster_filenames[closest_song_index]

        # Compute the similarity between the closest song and the unknown song
        similarity = cosine_similarity(unknown_song.reshape(1, -1), cluster_songs[closest_song_index].reshape(1, -1))

        return closest_song_index, closest_song_filename, similarity
    else:
        # Return None values if no matching song is found
        return None, None, None

def recognize_audio(audio_file_path):
    # Preprocess the audio file
    preprocessed_audio = preprocess_audio(audio_file_path)

    # Load the features from your own model
    database_songs = []
    song_objects = Music.objects.all()
    filenames = [os.path.basename(song.upload_file.path) for song in song_objects]
    for song in song_objects:
        song_features = preprocess_audio(song.upload_file.path)
        database_songs.append(song_features)

    # Determine the maximum number of frames among all the songs
    max_frames = max([song.shape[1] for song in database_songs])

    # Pad or truncate the songs to have the same number of frames
    database_songs = [np.pad(song, ((0, 0), (0, max_frames - song.shape[1]))).flatten() for song in database_songs]

    # Check if the preprocessed audio has more frames than the maximum number of frames
    if preprocessed_audio.shape[1] > max_frames:
        # Truncate the preprocessed audio to have the same number of frames as the maximum number of frames
        preprocessed_audio = preprocessed_audio[:, :max_frames]
    else:
        # Pad or truncate the preprocessed audio to have the same number of frames as the maximum number of frames
        preprocessed_audio = np.pad(preprocessed_audio, ((0, 0), (0, max_frames - preprocessed_audio.shape[1])))

    # Flatten the preprocessed audio array
    preprocessed_audio = preprocessed_audio.flatten()

    # Find the closest song in the database
    closest_song_index, closest_song_filename, similarity = find_closest_song(preprocessed_audio, database_songs, filenames)

    similarity_threshold = 0.3  # Adjust this value as needed
    if similarity is not None and similarity < similarity_threshold:
        print(f"Can't find any matching song in the database with a similarity of {similarity}")
        return None
    else:
        print(f"The closest song is '{closest_song_filename}' at index {closest_song_index} with a similarity of {similarity}")
        return closest_song_filename