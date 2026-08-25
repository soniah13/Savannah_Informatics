from datetime import timedelta, datetime
from django.utils import timezone
from ..models import Appointment, ClinicalService, Doctor, DoctorWorkingHours


Appointment_Duration = timedelta(minutes=30)
Booking_Notice = timedelta(hours=1)



# This function check if the doctor is available/scheduled to work during that predefined slot
# It returns a boolean value (True/False)
def Doctor_is_available_during_slot(doctor:Doctor, appointment_date, appointment_time):
    weekday = appointment_date.weekday()
    slot_start = appointment_time
    slot_end = (datetime.combine(appointment_date, appointment_time) + Appointment_Duration).time()

    return DoctorWorkingHours.objects.filter(doctor=doctor,
                                             weekday=weekday,
                                             start_time_lte = slot_start,
                                             end_time_gte = slot_end,).exists()


# check if doctor has an active appointment in this slot.
# cancelled appointments are ignored, making the slot available again
def doctor_has_conflicts(doctor:Doctor, appointment_date, appointment_time, exclude_apppointment_id=None):
    queryset = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        cancelled_at__isnull=True
        )
    # thisis used during rescheduling to prevent the appoinment from conflicting with itself
    if exclude_apppointment_id:
        queryset = queryset.exclude(id=exclude_apppointment_id)
    return queryset.exists()



# This function ensures that the appointment is atleast one hour from the current time.
def is_bookable_time(appointment_date, appointment_time):
    appointment_dateTime = timezone.make_aware(datetime.combine(appointment_date, appointment_time))
    minimum_booking_time = timezone.now() + Booking_Notice
    return appointment_dateTime >= minimum_booking_time

# Generate 30min slots that meet the set boundaries
def generate_slots(start_time, end_time):
    current =  datetime.combine(timezone.localdate(),start_time)
    end = datetime.combine(timezone.localdate(), end_time)

    slots = []

    while current + Appointment_Duration <= end:
        slots.append(current.time())
        current += Appointment_Duration
    return slots

#Function to return all open slots for a service on a given date where atleast 1 doctor is free
def get_doctor_available_slots(doctor, appointment_date):
    if appointment_date < timezone.localdate():
        return []
    weekday = appointment_date.weekday()
    working_hours = DoctorWorkingHours.objects.filter(doctor=doctor,weekday=weekday)
    available_slots = set()
    for working_hour in working_hours:
        slots = generate_slots(working_hour.start_time, working_hour.end_time)
        for slot in slots:
            if not is_bookable_time(appointment_date,slot):
                continue
            if doctor_has_conflicts(doctor, appointment_date, slot):
                continue
            available_slots.add(slot)
    return sorted(available_slots)

