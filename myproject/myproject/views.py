#from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
def homepage(request):
    #return HttpResponse("Welcome to my Homepage!")
    return render(request, 'home.html')
def aboutpage(request):
    ##return HttpResponse("This is my the About Page.")
    return render(request, 'about.html')

