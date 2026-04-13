import json
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .models import AvailabilitySlot, Booking
from accounts.models import DoctorProfile

@csrf_exempt
def api_doctor_slots(request):
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    doctor_profile = request.user.doctor_profile

    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            slot = AvailabilitySlot.objects.create(
                doctor=doctor_profile,
                date=data['date'],
                start_time=data['start_time'],
                end_time=data['end_time']
            )
            return JsonResponse({'success': True, 'slot_id': slot.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    # GET
    slots = AvailabilitySlot.objects.filter(doctor=doctor_profile).order_by('date', 'start_time')
    return JsonResponse({'slots': [
        {'id': s.id, 'date': s.date, 'start_time': str(s.start_time), 'end_time': str(s.end_time), 'is_booked': s.is_booked}
        for s in slots
    ]})

def api_patient_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'patient':
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    patient_profile = request.user.patient_profile
    today = timezone.now().date()
    
    available_slots = AvailabilitySlot.objects.filter(is_booked=False, date__gte=today).select_related('doctor')
    doctors_dict = {}
    for s in available_slots:
        if s.doctor.id not in doctors_dict:
            doctors_dict[s.doctor.id] = {
                'id': s.doctor.id,
                'name': s.doctor.user.get_full_name(),
                'specialization': s.doctor.specialization,
                'slots': []
            }
        doctors_dict[s.doctor.id]['slots'].append({
            'id': s.id, 'date': str(s.date), 'start_time': str(s.start_time)[:5]
        })

    my_bookings = Booking.objects.filter(patient=patient_profile).select_related('slot', 'slot__doctor')
    bookings_data = [{
        'doctor_name': b.slot.doctor.user.get_full_name(),
        'specialization': b.slot.doctor.specialization,
        'date': str(b.slot.date),
        'start_time': str(b.slot.start_time)[:5]
    } for b in my_bookings]

    return JsonResponse({
        'doctors': list(doctors_dict.values()),
        'bookings': bookings_data
    })

@csrf_exempt
def api_book_appointment(request, slot_id):
    if request.method != 'POST' or not request.user.is_authenticated or request.user.role != 'patient':
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        with transaction.atomic():
            slot = AvailabilitySlot.objects.select_for_update().get(id=slot_id)
            if slot.is_booked:
                return JsonResponse({'success': False, 'error': 'Slot already booked by someone else'})
                
            booking = Booking.objects.create(patient=request.user.patient_profile, slot=slot)
            slot.is_booked = True
            slot.save()
            
            # Google Calendar: create event for BOTH patient and doctor
            patient_gcal_link = None
            doctor_gcal_link = None
            try:
                from .gcal import create_calendar_event
                patient_gcal_link = create_calendar_event(request.user, booking, for_role='patient')
                print(f"[GCal] Patient event: {patient_gcal_link}")
            except Exception as e:
                print(f"[GCal] Failed to create patient event: {e}")
            
            try:
                from .gcal import create_calendar_event
                doctor_gcal_link = create_calendar_event(slot.doctor.user, booking, for_role='doctor')
                print(f"[GCal] Doctor event: {doctor_gcal_link}")
            except Exception as e:
                print(f"[GCal] Failed to create doctor event: {e}")
            
            # Email notification
            try:
                import requests
                requests.post('http://localhost:3000/send-email', json={
                    'action': 'BOOKING_CONFIRMATION',
                    'email': request.user.email,
                    'name': request.user.get_full_name(),
                    'doctor_name': slot.doctor.user.last_name,
                    'datetime': f"{slot.date} at {slot.start_time}"
                }, timeout=3)
            except Exception as e:
                print(f"[Email] Failed: {e}")

            return JsonResponse({
                'success': True,
                'gcal_link': patient_gcal_link,
                'doctor_gcal_link': doctor_gcal_link
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def api_google_login(request):
    import traceback
    try:
        role = request.GET.get('role', 'login')
        request.session['oauth_role'] = role
        from .gcal import get_authorization_url
        url = get_authorization_url(request)
        if url:
            return JsonResponse({'success': True, 'url': url})
        return JsonResponse({'success': False, 'error': 'Google credentials file not found or not configured'})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
