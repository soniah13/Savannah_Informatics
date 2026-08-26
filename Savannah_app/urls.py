from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet, DoctorViewSet, PatientViewSet



router = DefaultRouter()
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('doctors', DoctorViewSet, basename='doctor')
router.register('patients', PatientViewSet, basename='patient')

urlpatterns = router.urls
