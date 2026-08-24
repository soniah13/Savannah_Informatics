from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import Appointment


def cancel_appointment(appointment_date, appointment_time, reason:str):
    if Appointment.cancelled_at is not None:
        raise ValidationError("This appointment has already been cancelled")

    if Appointment.is_rescheduled:
        raise ValidationError("You cannot cancel a rescheduled appointment")

    Appointment.cancelled_at = timezone.now()
    Appointment.cancellation_reason = reason
    Appointment.save(update_fields=["cancelled_at, cancellation_reason"])

    return Appointment
