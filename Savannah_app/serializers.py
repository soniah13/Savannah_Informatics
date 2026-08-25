from rest_framework import serializers
from .models import *
from .services.bookings import create_appointment
from .exceptions import BookingError

class BookAppointmentSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    address = serializers.CharField()

