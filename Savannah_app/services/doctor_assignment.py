from ..models import Appointment
from .availability import get_eligible_doctors

# function to return the most recent doctor the patient saw for the clinical service, and considering any cancelled appointments
def get_previous_doctor(patient, clinical_service):
    previous_appointment = Appointment.objects.filter(
        patient=patient,
        clinical_service=clinical_service,
        cancelled_at__isnull=True,
    ).select_related("doctor").order_by(
        "-appointment_date","-appointment_time",
    ).first()
    return previous_appointment.doctor if previous_appointment else None

# function to get the most recent active appointment assigned to a doctor and ignore any cancelled appointments
def get_last_assignment(doctor):
    return Appointment.objects.filter(
        doctor=doctor,
        cancelled_at__isnull=True,
    ).order_by(
        "-appointment_date","-appointment_time",
    ).first()
