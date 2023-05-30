# Generated by Django 4.2.1 on 2023-05-30 10:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('musics', '0003_library_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userhistory',
            name='history_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='musics.history'),
        ),
        migrations.AlterField(
            model_name='userhistory',
            name='user_id',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
