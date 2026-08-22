from django.db import models

# Create your models here.
class Patient(models.Model):
    full_name = models.CharField(max_length=200)
    email=models.EmailField()
    phone_number=models.CharField(max_length=20)
    address=models.TextField()

    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name()

class Speciality(models.Model):
    speciality_name=models.CharField(max_length=100)
    speciality_description=models.TextField(blank=True)

    def __str__(self):
            return self.speciality_name()

class ClinicalService(models.Model):
    service_name=models.CharField(max_length=150)
    speciality=models.ForeignKey(Speciality,on_delete=models.PROTECT, related_name="clinical_services")
    service_description=models.TextField(blank=True)

    def __str__(self):
            return self.service_name()

class Doctor(models.Model):
    full_name=models.CharField(max_length=200)
    email=models.EmailField()
    phone_number=models.CharField(max_length=20)
    Specialities=models.ManyToManyField(Speciality, related_name='doctors')
    is_active=models.BooleanField(default=True)

    def __str__(self):
            return self.full_name()

class DoctorWorkingHours(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY=0,'Monday'
        TUESDAY=1,'Tuesday'
        WEDNESDAY=2, 'Wednesday'
        THURSDAY=3, 'Thursday'
        FRIDAY=4, 'Friday'
        SATURDAY=5, 'Saturday'
        SUNDAY=6, 'Sunday'
    doctor = models.ForeignKey(Doctor,on_delete=models.CASCADE,related_name='working_hours')
    weekday= models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

class Appointment(models.Model):
    patient= models.ForeignKey(Patient, on_delete=models.PROTECT,related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='appointments')
    clinical_services=models.ForeignKey(Speciality,on_delete=models.PROTECT, related_name='appointments')
    appointment_date=models.DateField()
    appointment_time=models.TimeField()
    additional_information=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
         constraints=[
              models.UniqueConstraint(fields=['doctor', 'appointment_date', 'appointment_time'],
                                      name='unique_doctor_appointment_slot')
         ]








