from django.db import models
from accounts.models import DoctorProfile, PatientProfile

class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')

    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}-{self.end_time}"

class Booking(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='bookings')
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.CASCADE, related_name='booking')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking: {self.patient} for {self.slot}"
