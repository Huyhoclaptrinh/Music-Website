from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.
def users(request):
    template = loader.get_template('main_menu.html')
    return HttpResponse(template.render())

def library(request):
    template = loader.get_template('library.html')
    return HttpResponse(template.render())

def newsfeed(request):
    template = loader.get_template('newsfeed.html')
    return HttpResponse(template.render())