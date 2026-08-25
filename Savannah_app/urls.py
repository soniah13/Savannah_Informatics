from django.urls import path
from .views import BookAppointmentView



urlpatterns = [
    path('appointments/', BookAppointmentView.as_view(), name="appointment"),
]
