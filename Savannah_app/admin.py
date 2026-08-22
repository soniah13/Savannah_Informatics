from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Patient)
admin.site.register(Speciality)
admin.site.register(ClinicalService)
admin.site.register(Doctor)
admin.site.register(DoctorWorkingHours)