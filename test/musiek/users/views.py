from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from posts.models import Post, Music
from users.models import UserRegister

def signIn(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Error")
            return redirect("/")

    return render(request, "authentication/sign_in.html")

def signUp(request):
    if request.method == "POST":
        name = request.POST["name"]
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        # repassword = request.POST["re_password"]
        gender = request.POST["gender"]
        birthday = request.POST["birthday"]
        avatar = request.POST["avatar"]
        wall = request.POST["wall"]
        errors = []

        if UserRegister.objects.filter(username=username).exists():
            errors.append("Username already exists! Please try a different username.")

        if UserRegister.objects.filter(email=email).exists():
            errors.append("Email is already registered.")

        if len(username) > 20:
            errors.append("Username must be under 20 characters.")

        if not username.isalnum():
            errors.append("Username must be alphanumeric.")

        if len(password) < 7:
            errors.append("Password must be at least 7 characters long.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("signup")
        
        user_register = UserRegister(email=email, fullname=name, username=username, password=password,gender=gender,birthday=birthday,avatar=avatar,wall=wall)
        # Set other fields as necessary
    
        user_register.set_password(user_register.password)
        user_register.save()
        
        messages.success(request, "Successful")

        return redirect("/")
    
    return render(request, "authentication/sign_up.html")


def signUpAuth(request):
    return render(request, "authentication/sign_up_auth.html")


def Home(request):
    music = Music.objects.first()
    context = {
        'music': music,
    }
    return render(request, "main_page/main_menu.html", context)


def Setting(request):
    return render(request, "main_page/settings.html")


def Profile(request):
    return render(request, "main_page/profile.html")
