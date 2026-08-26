from rest_framework.routers import DefaultRouter

from .views import (
	AppointmentViewSet,
	ClinicalServiceViewSet,
	DoctorViewSet,
	DoctorWorkingHoursViewSet,
	PatientViewSet,
	SpecialityViewSet,
)



router = DefaultRouter()
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('doctors', DoctorViewSet, basename='doctor')
router.register('patients', PatientViewSet, basename='patient')
router.register('working-hours', DoctorWorkingHoursViewSet, basename='working-hours')
router.register('specialities', SpecialityViewSet, basename='speciality')
router.register('clinical-services', ClinicalServiceViewSet, basename='clinical-service')

urlpatterns = router.urls
