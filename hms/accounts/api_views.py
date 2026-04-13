import json
import requests
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from .models import User, DoctorProfile, PatientProfile

@csrf_exempt
def api_signup_patient(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username') or data.get('email')
        password = data.get('password')
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists'})
        
        user = User.objects.create_user(
            username=username,
            email=data.get('email'),
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role='patient'
        )
        PatientProfile.objects.create(user=user)
        login(request, user)
        
        try:
            requests.post('http://localhost:3000/send-email', json={
                'action': 'SIGNUP_WELCOME',
                'email': user.email,
                'name': user.get_full_name() or user.username
            }, timeout=3)
        except:
            pass
            
        return JsonResponse({'success': True, 'role': 'patient', 'name': user.get_full_name()})
    return JsonResponse({'error': 'POST required'}, status=400)

@csrf_exempt
def api_signup_doctor(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username') or data.get('email')
        password = data.get('password')
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists'})
            
        user = User.objects.create_user(
            username=username,
            email=data.get('email'),
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role='doctor'
        )
        DoctorProfile.objects.create(user=user, specialization=data.get('specialization', 'General'))
        login(request, user)
        
        try:
            requests.post('http://localhost:3000/send-email', json={
                'action': 'SIGNUP_WELCOME',
                'email': user.email,
                'name': user.get_full_name() or user.username
            }, timeout=3)
        except:
            pass
            
        return JsonResponse({'success': True, 'role': 'doctor', 'name': user.get_full_name()})
    return JsonResponse({'error': 'POST required'}, status=400)

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(request, username=data.get('username'), password=data.get('password'))
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'role': user.role, 'name': user.get_full_name()})
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
    return JsonResponse({'error': 'POST required'}, status=400)

@csrf_exempt
def api_logout(request):
    logout(request)
    return JsonResponse({'success': True})

def api_me(request):
    if request.user.is_authenticated:
        has_gcal = False
        try:
            has_gcal = request.user.google_credential is not None
        except:
            pass
        return JsonResponse({'success': True, 'role': request.user.role, 'name': request.user.get_full_name(), 'has_gcal': has_gcal})
    return JsonResponse({'success': False}, status=401)
