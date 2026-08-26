from django.db import transaction
from rest_framework import serializers
from .models import Appointment, Doctor, DoctorWorkingHours, Patient
from .services.availability import get_doctor_available_slots
from .services.bookings import create_appointment, reschedule_appointment
from .exceptions import BookingError

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'email', 'phone_number', 'address']


class DoctorSerializer(serializers.ModelSerializer):
    working_hours = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'is_active',
            'working_hours',
        ]

    def get_working_hours(self, doctor):
        return DoctorWorkingHoursSerializer(
            doctor.working_hours.order_by('weekday', 'start_time'), many=True
        ).data

    def validate(self, attrs):
        schedule = self.initial_data.get('working_hours')
        if schedule is None:
            return attrs

        schedule_serializer = DoctorScheduleItemSerializer(data=schedule, many=True)
        schedule_serializer.is_valid(raise_exception=True)
        attrs['working_hours'] = schedule_serializer.validated_data
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        schedule = validated_data.pop('working_hours', [])
        doctor = Doctor.objects.create(**validated_data)
        DoctorWorkingHours.objects.bulk_create(
            [DoctorWorkingHours(doctor=doctor, **item) for item in schedule]
        )
        return doctor

    @transaction.atomic
    def update(self, instance, validated_data):
        schedule = validated_data.pop('working_hours', None)
        doctor = super().update(instance, validated_data)
        if schedule is not None:
            doctor.working_hours.all().delete()
            DoctorWorkingHours.objects.bulk_create(
                [DoctorWorkingHours(doctor=doctor, **item) for item in schedule]
            )
        return doctor


class DoctorScheduleItemSerializer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError(
                {'end_time': 'End time must be later than start time.'}
            )
        return attrs


class DoctorWorkingHoursSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)

    class Meta:
        model = DoctorWorkingHours
        fields = [
            'id', 'doctor', 'doctor_name', 'weekday', 'start_time', 'end_time'
        ]

    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError(
                {'end_time': 'End time must be later than start time.'}
            )
        return attrs

class BookAppointmentSerializer(serializers.Serializer):
    full_name=serializers.CharField(max_length=200)
    email=serializers.EmailField()
    phone_number=serializers.CharField(max_length=20)
    address=serializers.CharField()

    doctor_name = serializers.CharField()
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()
    additional_information = serializers.CharField(required=False, allow_blank=True)

    def validate_doctor_name(self, value):
        doctor = Doctor.objects.filter(full_name__iexact=value, is_active=True).first()
        if not doctor:
            raise serializers.ValidationError("Active doctor with this name does not exist")
        return doctor

    def validate(self, attrs):
        doctor = attrs['doctor_name']
        available_slots = get_doctor_available_slots(
            doctor, attrs['appointment_date']
        )
        if attrs['appointment_time'] not in available_slots:
            raise serializers.ValidationError({
                'appointment_time': (
                    'This slot is not available for the selected doctor and date.'
                )
            })
        return attrs

    def create(self, validated_data):
        doctor = validated_data.pop('doctor_name')

        try:
            appointment = create_appointment(
                doctor=doctor,
                full_name=validated_data.pop('full_name'),
                email=validated_data.pop('email'),
                phone_number=validated_data.pop('phone_number'),
                address=validated_data.pop('address'),
                appointment_date=validated_data.pop("appointment_date"),
                appointment_time=validated_data.pop("appointment_time"), 
                additional_information=validated_data.get("additional_information", "")

            )
            return appointment
        except BookingError as e:
            raise serializers.ValidationError(str(e))

class AppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'patient_name', 'doctor_name', 'appointment_date',
            'appointment_time', 'additional_information', 'cancelled_at',
            'cancellation_reason', 'is_rescheduled', 'created_at',
        ]




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