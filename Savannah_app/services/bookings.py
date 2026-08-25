from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError, transaction
from ..models import Appointment, Patient
from .availability import is_bookable_time
from .doctor_assignment import assign_doctor
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
    clinical_service,
    appointment_date,
    appointment_time,
    additional_information="",
):
    if appointment_date < timezone.localdate():
        raise InvalidBookingError(
            "Appointment date cannot be in the past."
        )

    if not is_bookable_time(
        appointment_date,
        appointment_time,
    ):
        raise InvalidBookingError(
            "Appointments must be booked at least one hour in advance."
        )

    patient = get_or_create_patient(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        address=address,
    )

    doctor = assign_doctor(
        patient=patient,
        clinical_service=clinical_service,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
    )

    if doctor is None:
        raise SlotUnavailableError(
            "The selected appointment slot is no longer available."
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
        raise ConflictError(
            "The selected appointment slot was booked by another request."
        ) from exc

    return appointment

@transaction.atomic
def cancel_appointment(
    appointment,
    reason,
):
    if appointment.cancelled_at is not None:
        raise AppointmentCancelledError(
            "This appointment has already been cancelled."
        )

    appointment.cancelled_at = timezone.now()
    appointment.cancellation_reason = reason

    appointment.save(
        update_fields=[
            "cancelled_at",
            "cancellation_reason",
        ]
    )

    return appointment

def cancel_appointment(appointment_date, appointment_time, reason:str):
    if Appointment.cancelled_at is not None:
        raise ValidationError("This appointment has already been cancelled")

    if Appointment.is_rescheduled:
        raise ValidationError("You cannot cancel a rescheduled appointment")

    Appointment.cancelled_at = timezone.now()
    Appointment.cancellation_reason = reason
    Appointment.save(update_fields=["cancelled_at, cancellation_reason"])

    return Appointment
