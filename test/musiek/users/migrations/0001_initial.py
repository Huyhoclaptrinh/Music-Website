# Generated by Django 4.2.1 on 2023-05-18 08:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('musics', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRegister',
            fields=[
                ('user_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fullname', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('dob', models.DateField(auto_now_add=True)),
                ('gender', models.CharField(blank=True, choices=[('MALE', 'Male'), ('FEMALE', 'Female')], max_length=10)),
                ('ava', models.ImageField(default=None, upload_to='static/img')),
                ('wall', models.ImageField(default=None, upload_to='static/img')),
            ],
        ),
        migrations.CreateModel(
            name='UserLibrary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('library_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musics.library')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userregister')),
            ],
        ),
        migrations.CreateModel(
            name='UserHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('history_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musics.history')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userregister')),
            ],
        ),
        migrations.CreateModel(
            name='FriendRecommend',
            fields=[
                ('data_id', models.AutoField(primary_key=True, serialize=False)),
                ('meta_data', models.IntegerField(default=None)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userregister')),
            ],
        ),
    ]
