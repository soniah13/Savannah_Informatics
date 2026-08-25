from rest_framework import serializers
from .models import Patient, Doctor, Appointment
from .services.bookings import create_appointment, reschedule_appointment
from .exceptions import BookingError

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'email', 'phone_number', 'address']

class BookAppointmentSerializer(serializers.Serializer):
    full_name=serializers.CharField(max_length=200)
    email=serializers.EmailField()
    phone_number=serializers.CharField(max_length=20)
    address=serializers.CharField()

    doctor_name = serializers.CharField()
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()
    additional_information = serializers.CharField(required=False, allow_blank=True)

    def validate_doctor_id(self, value):
            # using both filter and first just incase doctors share a name
        doctor =  Doctor.objects.filter(full_name__isexact=value, is_active=True).firt()
        if not doctor:
            raise serializers.ValidationError("Active doctor with this name does not exist")
        return doctor

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

class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5, error_messages={
        "required":"You must provide a cancellation reason",
        "blank":"Cancellation reason cannot be empty"
    })

class RescheduleAppointmentSerializer(serializers.Serializer):
    appointment_date = serializers.DateField(required=True)
    appointment_time = serializers.TimeField(required=True)

    def update(self, instance, validated_data):
        try:
            return reschedule_appointment(
                appointment=instance, new_date=validated_data['appointment_date'], new_time=validated_data['appointment_time']
            )
        except BookingError as e:
            raise serializers.ValidationError(str(e))