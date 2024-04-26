from django.shortcuts import render
# Create your views here.

def profile(requests):
    context = {}
    return render(requests, 'profile.html', context)
