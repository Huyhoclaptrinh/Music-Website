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

        user = authenticate(username=username,password=password)

        if user is not None:
           login(request,user)
           u_name = user.username
           return render(request,'main_menu.html',{'username':u_name})
        else:
           messages.error(request,"Error")
           return redirect('signin')
    
    return render(request,'sign_in.html')

def signUp(request):
    if request.method == "POST":
        name = request.POST['name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! Please try some other username.")
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('signup')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('signup')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('signup')
        
        if len(password)<7:
           messages.error(request,"Password must be more than 7 characters!!")
           return redirect('signup')

        myuser = User.objects.create_user(username, email,password)
        myuser.name = name

        myuser.save()

        messages.success(request,"Successfull")
        return redirect('signin')

    return render(request,'sign_up.html')

def signUpAuth(request):
  return render(request,'sign_up_auth.html')

def Home(request):
  return render(request,'main_menu.html')

def Newsfeed(request):
  return render(request,'newsfeed.html')

def Library(request):
  return render(request,'library.html')

def Setting(request):
  return render(request,'settings.html')

def Profile(request):
  return render(request,'profile.html')

def Upload(request):
  return render(request,'upload.html')

# class SignUpForm(forms.ModelForm):
#     class Meta:
#         model = userRegister
#         fields = ['fullname', 'username', 'email', 'password']
#         widgets = {
#             'password': forms.PasswordInput
#         }

# def form_submit_view(request):
#     if request.method == 'POST':
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             form.save()  # Save the form data to the database

#             # Redirect to a success page or perform any additional actions

#     else:
#         form = SignUpForm()

#     return render(request, 'sign_up.html', {'form': form})


