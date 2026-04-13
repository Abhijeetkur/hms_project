from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import DoctorSignUpForm, PatientSignUpForm
import requests

def signup_doctor(request):
    if request.method == 'POST':
        form = DoctorSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            try:
                requests.post('http://localhost:3000/send-email', json={
                    'action': 'SIGNUP_WELCOME',
                    'email': user.email,
                    'name': user.get_full_name() or user.username
                }, timeout=3)
            except:
                pass
            return redirect('dashboard')
    else:
        form = DoctorSignUpForm()
    return render(request, 'accounts/signup.html', {'form': form, 'role': 'Doctor'})

def signup_patient(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            try:
                requests.post('http://localhost:3000/send-email', json={
                    'action': 'SIGNUP_WELCOME',
                    'email': user.email,
                    'name': user.get_full_name() or user.username
                }, timeout=3)
            except:
                pass
            return redirect('dashboard')
    else:
        form = PatientSignUpForm()
    return render(request, 'accounts/signup.html', {'form': form, 'role': 'Patient'})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    if request.user.is_doctor():
        return redirect('doctor_dashboard')
    else:
        return redirect('patient_dashboard')
