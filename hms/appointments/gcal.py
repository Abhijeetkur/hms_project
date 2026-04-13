import os
import json
import datetime
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from accounts.models import User, GoogleCredential, DoctorProfile, PatientProfile

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]
CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'client_secret_274411568609-9f41n388v27csqh42g6p2todigdqghmq.apps.googleusercontent.com.json')
REDIRECT_URI = 'http://localhost:8000/google/callback/'

def get_authorization_url(request):
    if not os.path.exists(CREDENTIALS_FILE):
        return None
        
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    request.session['state'] = state
    request.session['code_verifier'] = flow.code_verifier
    return authorization_url

def handle_callback(request):
    state = request.session.get('state')
    code_verifier = request.session.get('code_verifier')
    
    if not os.path.exists(CREDENTIALS_FILE):
        return None
        
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
        code_verifier=code_verifier
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    oauth2_client = build('oauth2', 'v2', credentials=credentials)
    user_info = oauth2_client.userinfo().get().execute()
    email = user_info.get('email')
    
    # Try to find existing user, or create new based on session role preference
    user = User.objects.filter(email=email).first()
    role_pref = request.session.get('oauth_role', 'login')
    
    if not user:
        if role_pref == 'login':
            role_pref = 'patient'  # default fallback
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            role=role_pref
        )
        if role_pref == 'doctor':
            DoctorProfile.objects.create(user=user, specialization='General')
        else:
            PatientProfile.objects.create(user=user)
            
        try:
            import requests
            requests.post('http://localhost:3000/send-email', json={
                'action': 'SIGNUP_WELCOME',
                'email': user.email,
                'name': user.get_full_name() or user.username
            }, timeout=3)
            print(f"[Email] Sent welcome email to {user.email}")
        except Exception as e:
            print(f"[Email] Failed to send welcome email: {e}")
    else:
        # If user exists, dynamically switch their role to what they explicitly requested
        if role_pref in ['doctor', 'patient'] and user.role != role_pref:
            user.role = role_pref
            user.save()
            # Ensure proper profile exists
            if role_pref == 'doctor' and not hasattr(user, 'doctor_profile'):
                DoctorProfile.objects.create(user=user, specialization='General')
            elif role_pref == 'patient' and not hasattr(user, 'patient_profile'):
                PatientProfile.objects.create(user=user)


    GoogleCredential.objects.update_or_create(
        user=user,
        defaults={
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': json.dumps(credentials.scopes),
        }
    )
    return user

def create_calendar_event(user, booking, for_role='patient'):
    try:
        creds_obj = user.google_credential
        creds = Credentials(
            token=creds_obj.token,
            refresh_token=creds_obj.refresh_token,
            token_uri=creds_obj.token_uri,
            client_id=creds_obj.client_id,
            client_secret=creds_obj.client_secret,
            scopes=json.loads(creds_obj.scopes)
        )
        service = build('calendar', 'v3', credentials=creds)

        import datetime
        
        # Let Google Calendar use the explicit timeZone parameter below instead of confusing it with hardcoded offsets
        start_datetime = f"{booking.slot.date.isoformat()}T{booking.slot.start_time.strftime('%H:%M:%S')}"
        end_datetime = f"{booking.slot.date.isoformat()}T{booking.slot.end_time.strftime('%H:%M:%S')}"

        doctor_name = booking.slot.doctor.user.get_full_name()
        patient_name = booking.patient.user.get_full_name()

        if for_role == 'doctor':
            title = f'Appointment with {patient_name}'
            description = f'Patient: {patient_name}\nTime: {booking.slot.start_time} - {booking.slot.end_time}'
        else:
            title = f'Appointment with Dr. {doctor_name}'
            description = f'Doctor: Dr. {doctor_name}\nSpecialization: {booking.slot.doctor.specialization}\nTime: {booking.slot.start_time} - {booking.slot.end_time}'

        event = {
          'summary': title,
          'description': description,
          'start': {
            'dateTime': start_datetime,
            'timeZone': 'Asia/Kolkata',
          },
          'end': {
            'dateTime': end_datetime,
            'timeZone': 'Asia/Kolkata',
          },
        }
        
        print(f"[GCal] Sending event to Google for {for_role}:")
        print(f"  Start: {start_datetime}")
        print(f"  End:   {end_datetime}")
        print(f"  Payload: {json.dumps(event, indent=2)}")

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"[GCal] Created event for {user.username}: {created_event.get('htmlLink')}")
        return created_event.get('htmlLink')
    except Exception as e:
        print(f"[GCal] Failed to create event for {user.username}: {e}")
        return None

