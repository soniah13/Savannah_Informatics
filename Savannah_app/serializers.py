from rest_framework import serializers
from .models import Patient, Doctor, Appointment
from .services.bookings import create_appointment
from .exceptions import BookingError

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'email', 'phone_number', 'address']

class BookAppointmentSerializer(serializers.Serializer):
    patient = PatientSerializer()
    doctor_id = serializers.IntegerField()
    appointment_date = serializers.DateTimeField()
    appointment_time = serializers.TimeField()
    additional_information = serializers.CharField(required=False, allow_blank=True)

    def validate_doctor_id(self, value):
        try:
            return Doctor.objects.get(id=value, is_active=True)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Active doctor with this ID does not exist")


    def create(self, validated_data):
        patient_data = validated_data.pop('patient')
        doctor = validated_data.pop('doctor_id')

        try:
            appointment = create_appointment(
                doctor=doctor,
                full_name=patient_data['full_name'],
                email=patient_data['email'],
                phone_number=patient_data['phone_number'],
                address=patient_data['address'],
                **validated_data

            )
            return appointment
        except BookingError as e:
            raise serializers.ValidationError(str(e))

# serializer that makes doctors name readable and gives appoinment booking response cleaner
class AppointmentResponseSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    class Meta:
        model = Appointment
        fields = ['id', 'appointment_date', 'appointment_time', 'doctor_name', "is_rescheduled", 'cancelled_at']

