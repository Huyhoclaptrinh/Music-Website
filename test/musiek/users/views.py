from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from posts.models import Post, Music
from users.models import UserRegister
from musics.models import History, UserHistory
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
# from posts.preprocessing import make_recommendations, build_recommendation_model
from posts.preprocessing2 import preprocess_data, tune_hyperparameters, train_model, make_recommendations


def signIn(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                # Redirect superuser to Django admin
                return redirect('admin:index')
            else:
                # Redirect regular user to home page
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
            return redirect("signin")
    
    storage = messages.get_messages(request)
    storage.used = True

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
        messages.success(request, "Successfully created account: " + username + ". Please log in!")

        return redirect("signin")
    
    storage = messages.get_messages(request)
    storage.used = True
    
    return render(request, "authentication/sign_up.html")

def signOut(request):
    logout(request)
    return redirect('signin')

def signUpAuth(request):
    return render(request, "authentication/sign_up_auth.html")


def Home(request):
    try:
        user_history = UserHistory.objects.get(user_id=request.user)
        history = user_history.history_id
        is_creator = user_history.user_id == request.user

        if history:
            songs = history.historyentry_set.order_by('-date')[:3]
        else:
            songs = []

    except ObjectDoesNotExist:
        user_history = None
        history = None
        is_creator = False
        songs = []
    trainset = preprocess_data()
    model, rmse = tune_hyperparameters(trainset)
    trained_model = train_model(trainset, model)

    user_id = request.user  # Replace with the actual user ID
    recommendations = make_recommendations(user_id, trained_model, top_n=5)
   
    # user = UserRegister.objects.get(user_id=user_id)
    
    context = {
        'user_history': user_history,
        'history': history,
        'is_creator': is_creator,
        'songs': songs,
        # 'user': user,
        'recommendations': recommendations,
    }
    return render(request, "main_page/main_menu.html", context)


def Setting(request):
    return render(request, "main_page/settings.html")

# def right_sidebar(request):
#     user = request.user
#     user_history = UserHistory.objects.filter(user_id=user).first()
    
#     if user_history:
#         history = History.objects.filter(userhistory__user_id=user).order_by('-date')[:3]
#     else:
#         history = []

#     context = {
#         'history': history,
#     }
#     return render(request, 'base/base-right-content.html', context)