from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages

def signIn(request):
  if request.method == "POST":
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
      login(request, user)
      return redirect("home")
    else:
      messages.error(request,"Error")
      return redirect('/')
  
  return render(request,'sign_in.html')

def signUp(request):
  if request.method == "POST":
    name = request.POST['name']
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    errors = []
    if User.objects.filter(username=username):
      errors.append("Username already exist! Please try some other username.")
    
    if User.objects.filter(email=email).exists():
      errors.append("Email Already Registered!!")
    
    if len(username)>20:
      errors.append("Username must be under 20 charcters!!")
    
    if not username.isalnum():
      errors.append("Username must be Alpha-Numeric!!")
    
    if len(password)<7:
      errors.append("Password must be more than 7 characters!!")
    
    if errors:
      for error in errors:
        messages.error(request, error)
        return redirect('signup')
      
    myuser = User.objects.create_user(username, email, password)
    myuser.name = name
    myuser.save()
    messages.success(request, "Successful")

    return redirect('/')
  return render(request,'sign_up.html')

def signUpAuth(request):
  return render(request,'sign_up_auth.html')

def Home(request):
  return render(request,'main_menu.html')

def Setting(request):
  return render(request,'settings.html')

def Profile(request):
  return render(request,'profile.html')


