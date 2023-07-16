import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files import File
from posts.models import Music
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Imports .mp3 files into the Music model.'

    def handle(self, *args, **options):
        audio_base_path = 'media/audio_base'
        img_base_path = 'media/img_base'

        # Iterate over .mp3 files in audio_base_path
        for file_name in os.listdir(audio_base_path):
            if file_name.endswith('.mp3'):
                mp3_path = os.path.join(audio_base_path, file_name)

                # Check if the file already exists in the Music model
                if Music.objects.filter(upload_file__icontains=file_name).exists():
                    self.stdout.write(f'Skipping import of "{file_name}" as it already exists.')
                    continue

                mp3_file = File(open(mp3_path, 'rb'))

                # Extract name and author from file name
                name_author = os.path.splitext(file_name)[0]
                name, author = name_author.split('_')

                # Find corresponding image file in img_base_path
                img_file_name = f"{name_author}.jpg"  # Assuming jpg format
                img_path = os.path.join(img_base_path, img_file_name)

                if os.path.exists(img_path):
                    # Create a new Music object and save it
                    music = Music(name=name, author=author)

                    # Save the MP3 file to media/audio directory
                    music.upload_file.save(file_name, mp3_file, save=True)

                    # Open the image file and assign it to the music object
                    with open(img_path, 'rb') as img_file:
                        music.img.save(img_file_name, ContentFile(img_file.read()), save=True)

        self.stdout.write(self.style.SUCCESS('Music files imported successfully.'))
