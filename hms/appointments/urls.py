from django.urls import path
from . import api_views, views

urlpatterns = [
    path('', views.home, name='home'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('book/<int:slot_id>/', views.book_appointment, name='book_appointment'),

    path('api/doctor/slots/', api_views.api_doctor_slots),
    path('api/patient/dashboard/', api_views.api_patient_dashboard),
    path('api/book/<int:slot_id>/', api_views.api_book_appointment),
    path('api/google/login/', api_views.api_google_login),
    
    # Direct browser navigation (not AJAX) for OAuth flow
    path('google/login/', views.google_auth_redirect, name='google_login'),
    path('google/callback/', views.google_calendar_callback, name='google_callback'),
]

