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

# function to choose a doctor who has gone longest without an appointment
# and give priority to doctors who have never been assigned
def choose_by_rotation(doctors):
    never_assigned = []
    assigned = []
    for doctor in doctors:
        last_appointment = get_last_assignment(doctor)
        if not last_appointment:
            never_assigned.append(doctor)
        else:
            assigned.append((
                doctor, 
                last_appointment.appointment_date,
                last_appointment.appointment_time
            ))
    # give priority to doctors with zero appointment
    if never_assigned:
        return never_assigned[0]
    # sort assigned doctors by oldest appointment date/time first
    assigned.sort(key=lambda item:(item[1], item[2]))

    # return the doctor from the oldest assignement to the lastest assignement
    return assigned[0][0]

