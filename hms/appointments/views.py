from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import AvailabilitySlot, Booking
from .forms import AvailabilitySlotForm
from accounts.models import DoctorProfile

def home(request):
    if request.user.is_authenticated:
        if request.user.is_doctor():
            return redirect('doctor_dashboard')
        return redirect('patient_dashboard')
    return render(request, 'home.html')

@login_required
def doctor_dashboard(request):
    try:
        doctor_profile = request.user.doctor_profile
    except:
        return redirect('dashboard') # Not a doctor

    if request.method == 'POST':
        form = AvailabilitySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = doctor_profile
            # Basic validation to avoid duplicate slots handled by Meta unique_together
            try:
                slot.save()
                messages.success(request, "Availability slot added successfully!")
            except Exception as e:
                messages.error(request, "Could not add slot. Check for overlapping timings.")
            return redirect('doctor_dashboard')
    else:
        form = AvailabilitySlotForm()

    slots = AvailabilitySlot.objects.filter(doctor=doctor_profile).order_by('date', 'start_time')
    
    context = {
        'form': form,
        'slots': slots
    }
    return render(request, 'appointments/doctor_dashboard.html', context)

@login_required
def patient_dashboard(request):
    try:
        patient_profile = request.user.patient_profile
    except:
        return redirect('dashboard') # Not a patient

    # Get doctors that have future available slots
    # For simplicity, filtering slots that are not booked and >= today
    today = timezone.now().date()
    doctors = DoctorProfile.objects.all()
    available_slots = AvailabilitySlot.objects.filter(
        is_booked=False,
        date__gte=today
    ).select_related('doctor').order_by('date', 'start_time')

    # Group slots by doctor for easier template rendering
    doctors_with_slots = []
    for doctor in doctors:
        d_slots = [s for s in available_slots if s.doctor_id == doctor.id]
        if d_slots:
            doctors_with_slots.append({'doctor': doctor, 'slots': d_slots})

    # Show patient bookings
    my_bookings = Booking.objects.filter(patient=patient_profile).select_related('slot', 'slot__doctor')

    context = {
        'doctors_with_slots': doctors_with_slots,
        'my_bookings': my_bookings
    }
    return render(request, 'appointments/patient_dashboard.html', context)

@login_required
def book_appointment(request, slot_id):
    if request.method != 'POST':
        return redirect('patient_dashboard')

    try:
        patient_profile = request.user.patient_profile
    except:
        return redirect('dashboard')

    try:
        # Atomic transaction + select_for_update to avoid race conditions!
        with transaction.atomic():
            slot = AvailabilitySlot.objects.select_for_update().get(id=slot_id)
            if slot.is_booked:
                messages.error(request, "Sorry, this slot was just booked by someone else.")
            else:
                booking = Booking.objects.create(patient=patient_profile, slot=slot)
                slot.is_booked = True
                slot.save()
                messages.success(request, f"Successfully booked appointment with Dr. {slot.doctor.user.last_name} for {slot.date} at {slot.start_time}.")
                
                import requests
                
                # 1. Send confirmation to Patient
                try:
                    requests.post('http://localhost:3000/send-email', json={
                        'action': 'BOOKING_CONFIRMATION',
                        'email': request.user.email,
                        'name': request.user.get_full_name() or request.user.username,
                        'doctor_name': slot.doctor.user.last_name,
                        'datetime': f"{slot.date} at {slot.start_time}"
                    }, timeout=10)
                except Exception as e:
                    print(f"Could not send email to patient: {e}")
                
                # 2. Send notification to Doctor
                try:
                    requests.post('http://localhost:3000/send-email', json={
                        'action': 'DOCTOR_NOTIFICATION',
                        'email': slot.doctor.user.email,
                        'name': slot.doctor.user.last_name,
                        'patient_name': request.user.get_full_name() or request.user.username,
                        'datetime': f"{slot.date} at {slot.start_time}"
                    }, timeout=10)
                    print(f"[Email] Booking notifications sent to {request.user.email} and {slot.doctor.user.email}")
                except Exception as e:
                    print(f"Could not send email to doctor: {e}")
                
                try:
                    from .gcal import create_calendar_event
                    # Patient event
                    create_calendar_event(request.user, booking, for_role='patient')
                    # Doctor event
                    create_calendar_event(slot.doctor.user, booking, for_role='doctor')
                    messages.info(request, f"Added to your Google Calendar!")
                except Exception as e:
                    print("Could not create calendar event:", e)

                
    except AvailabilitySlot.DoesNotExist:
        messages.error(request, "Slot not found.")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('patient_dashboard')

def google_auth_redirect(request):
    """Browser navigates here directly (not via AJAX). Stores role in session, redirects to Google."""
    import traceback
    try:
        role = request.GET.get('role', 'login')
        request.session['oauth_role'] = role
        from .gcal import get_authorization_url
        url = get_authorization_url(request)
        if url:
            return redirect(url)
        return redirect('login')
    except Exception as e:
        traceback.print_exc()
        return redirect('login')

def google_calendar_callback(request):
    """Google redirects here after consent. Same port = same session = state works."""
    import traceback
    from django.contrib.auth import login
    try:
        from .gcal import handle_callback
        user = handle_callback(request)
        if user:
            login(request, user)
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            else:
                return redirect('patient_dashboard')
    except Exception as e:
        traceback.print_exc()
    return redirect('login')
