from datetime import timedelta, datetime
from django.utils import timezone
from models import *


Appointment_Duration = timedelta(minutes=30)
Booking_Notice = timedelta(hours=1)



# This function check if the doctor is available/scheduled to work during that precified slot
# It returns a boolean value (True/False)
def Doctor_is_available_slot(doctor:Doctor, appointment_date, appointment_time):
    weekday = appointment_date.weekday()
    slot_start = appointment_time
    slot_end = (datetime.combine(appointment_date, appointment_time) + Appointment_Duration).time()

    return DoctorWorkingHours.objects.filter(doctor=doctor,
                                             weekday=weekday,
                                             start_time_lte = slot_start,
                                             end_time_gte = slot_end,).exists()


# Since every appointment is 30min, matching the same doctor/date and time is enough to use to detect a conflict
def conflicting_appointment(doctor:Doctor, appointment_date, appointment_time):
    return Appointment.objects.filter(doctor=doctor,
                                      appointment_date=appointment_date,
                                      appointment_time=appointment_time).exists()


# returns doctors whocan serve the requested slot depending on their speciality and service requested
# by checking if doctor is active, has required speciality, works during the requested slot and has no existing appointment in the slot
def get_eligible_doctors(clinical_service:ClinicalService, appointment_date, appointment_time):
    doctors = (Doctor.objects.filter(Specialities=clinical_service.speciality, is_active=True,).distinct())
    eligible_doctors = []
    for doctor in doctors:
        if not Doctor_is_available_slot(doctor, appointment_date, appointment_time):
            continue
        if conflicting_appointment(doctor, appointment_date, appointment_time):
            continue
        eligible_doctors.append(doctor)
    return eligible_doctors


# This function ensures that the appointment is atleast one hour from the current time.
def appointment_atleast_one_hour_ahead(appointment_date, appointment_time):
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

#Function to return all current bookable slots on a given date
def get_available_slots(clinical_service:ClinicalService, appointment_date):
    if appointment_date < timezone.localdate():
        return []
    weekday = appointment_date.weekday()
    working_hours = DoctorWorkingHours.objects.filter(weekday=weekday, doctor__speciality=clinical_service.speciality, doctor__is_active=True).distinct()
    available_slots = set()
    for working_hour in working_hours:
        slots = generate_slots(working_hour.start_time, working_hour.end_time)
        for slot in slots:
            if not appointment_atleast_one_hour_ahead(appointment_date,slot):
                continue
            eligible_doctors = get_eligible_doctors(clinical_service=clinical_service, appointment_date=appointment_date, appointment_time=slot)
            if eligible_doctors: 
                available_slots.add(slot)
    return sorted(available_slots)

