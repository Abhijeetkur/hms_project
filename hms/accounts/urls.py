from django.urls import path
from . import api_views, views

urlpatterns = [
    path('signup/patient/', views.signup_patient, name='signup_patient'),
    path('signup/doctor/', views.signup_doctor, name='signup_doctor'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API endpoints
    path('api/signup/patient/', api_views.api_signup_patient),
    path('api/signup/doctor/', api_views.api_signup_doctor),
    path('api/login/', api_views.api_login),
    path('api/logout/', api_views.api_logout),
    path('api/me/', api_views.api_me),
]

