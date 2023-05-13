from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

def signIn(request):
  template = loader.get_template('sign_in.html')
  return HttpResponse(template.render())

def signUp(request):
  template = loader.get_template('sign_up.html')
  return HttpResponse(template.render())

def signUpAuth(request):
  template = loader.get_template('sign_up_auth.html')
  return HttpResponse(template.render())

def Home(request):
  template = loader.get_template('main_menu.html')
  return HttpResponse(template.render())

def Newsfeed(request):
  template = loader.get_template('newsfeed.html')
  return HttpResponse(template.render())

def Library(request):
  template = loader.get_template('library.html')
  return HttpResponse(template.render())

def Setting(request):
  template = loader.get_template('settings.html')
  return HttpResponse(template.render())

def Profile(request):
  template = loader.get_template('profile.html')
  return HttpResponse(template.render())

def Upload(request):
  template = loader.get_template('upload.html')
  return HttpResponse(template.render())
