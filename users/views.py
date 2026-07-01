from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm


# -------------------
# HOME PAGE
# -------------------
def home(request):
    return render(request, "users/home.html")


# -------------------
# REGISTER
# -------------------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


# -------------------
# LOGIN
# -------------------
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form})


# -------------------
# LOGOUT
# -------------------
def logout_view(request):
    logout(request)
    return redirect("login")


# -------------------
# DASHBOARD (PROTECTED)
# -------------------
@login_required
def dashboard(request):
    return render(request, "users/dashboard.html")