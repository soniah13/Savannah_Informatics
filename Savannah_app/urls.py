from rest_framework.routers import DefaultRouter

from .views import (
	AppointmentViewSet,
	DoctorViewSet,
	DoctorWorkingHoursViewSet,
	PatientViewSet,
)



router = DefaultRouter()
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('doctors', DoctorViewSet, basename='doctor')
router.register('patients', PatientViewSet, basename='patient')
router.register('working-hours', DoctorWorkingHoursViewSet, basename='working-hours')

urlpatterns = router.urls
