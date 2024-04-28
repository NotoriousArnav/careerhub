from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserProfile
# Create your views here.

def index(req):
    return render(req, 'index.html')

@login_required(login_url="/accounts/login")
def profile(req):
    profile = UserProfile.objects.filter(user=req.user).first()
    context = {
        "profile": profile
    }
    print(profile)
    return render(req, 'profile.html', context)
