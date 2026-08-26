from django.utils import timezone
from django.db import IntegrityError, transaction
from ..models import Appointment, ClinicalService, Patient
from .availability import is_bookable_time, Doctor_is_available_during_slot, doctor_has_conflicts
from ..exceptions import AppointmentCancelledError, ConflictError, InvalidBookingError, SlotUnavailableError


def get_or_create_patient(full_name, email, phone_number,address):
    patient, created = Patient.objects.get_or_create(
        email=email,
        defaults={
            "full_name":full_name,
            "phone_number":phone_number,
            "address":address,
        },
    )
    if not created:
        patient.full_name = full_name
        patient.phone_number = phone_number
        patient.address = address
        patient.save(
            update_fields=["full_name","phone_number","address"]
        )
    return patient

@transaction.atomic
def create_appointment(
    *,
    full_name,
    email,
    phone_number,
    address,
    doctor,
    clinical_service: ClinicalService,
    appointment_date,
    appointment_time,
    additional_information="",
):
    if appointment_date < timezone.localdate():
        raise InvalidBookingError("Appointment date cannot be in the past.")
        
    if not is_bookable_time(appointment_date, appointment_time):
        raise InvalidBookingError("Appointments must be booked at least one hour in advance.")

    # Validate that the requested doctor is working and free
    if not Doctor_is_available_during_slot(doctor, appointment_date, appointment_time):
        raise SlotUnavailableError("Doctor is not scheduled to work during this time.")
        
    if doctor_has_conflicts(doctor, appointment_date, appointment_time):
        raise ConflictError("The selected appointment slot is already booked.")

    patient = get_or_create_patient(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        address=address,
    )

    try:
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            clinical_service=clinical_service,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            additional_information=additional_information,
        )
    except IntegrityError as exc:
        raise ConflictError( "The selected appointment slot was booked by another request.") from exc

    return appointment

@transaction.atomic
def cancel_appointment(appointment, reason):
    if appointment.cancelled_at is not None:
        raise AppointmentCancelledError("This appointment has already been cancelled.")
        
    appointment.cancelled_at = timezone.now()
    appointment.cancellation_reason = reason
    appointment.save(
        update_fields=[
            "cancelled_at",
            "cancellation_reason",
        ]
    )
    return appointment

@transaction.atomic
def reschedule_appointment(appointment, new_date, new_time, doctor=None):
    if appointment.cancelled_at is not None:
        raise InvalidBookingError("You cannot reschedule a cancelled appointment")
    if new_date < timezone.localdate():
        raise InvalidBookingError("Appointment date cannot be in the past")
    if not is_bookable_time(new_date, new_time):
        raise InvalidBookingError("Appointment must be booked atleast one hour in advance")
    doctor = doctor or appointment.doctor
    if (
        appointment.clinical_service
        and not doctor.Specialities.filter(
            pk=appointment.clinical_service.speciality_id
        ).exists()
    ):
        raise InvalidBookingError(
            "The selected doctor does not provide this appointment's service."
        )
    if not Doctor_is_available_during_slot(doctor, new_date, new_time):
        raise SlotUnavailableError("The soctor does not work during this time slot either choose another doctor or another slot")

    if doctor_has_conflicts(
        doctor,
        new_date,
        new_time,
        exclude_apppointment_id=appointment.id,
    ):
        raise ConflictError("The selected appointment slot is already booked.")

    appointment.appointment_date = new_date
    appointment.appointment_time = new_time
    appointment.doctor = doctor
    appointment.is_rescheduled = True
    appointment.save(update_fields=['appointment_date', 'appointment_time', 'doctor', 'is_rescheduled'])

    return appointment
