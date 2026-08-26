from django.db import transaction
from rest_framework import serializers
from .models import (
    Appointment,
    ClinicalService,
    Doctor,
    DoctorWorkingHours,
    Patient,
    Speciality,
)
from .services.availability import get_doctor_available_slots
from .services.bookings import create_appointment, reschedule_appointment
from .exceptions import BookingError

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['full_name', 'email', 'phone_number', 'address']


class DoctorSerializer(serializers.ModelSerializer):
    working_hours = serializers.SerializerMethodField()
    specialities = serializers.PrimaryKeyRelatedField(
        source='Specialities',
        many=True,
        queryset=Speciality.objects.all(),
    )

    class Meta:
        model = Doctor
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'is_active',
            'specialities', 'working_hours',
        ]

    def get_working_hours(self, doctor):
        return DoctorWorkingHoursSerializer(
            doctor.working_hours.order_by('weekday', 'start_time'), many=True
        ).data

    def validate(self, attrs):
        specialities = attrs.get('Specialities')
        if specialities is not None and not specialities:
            raise serializers.ValidationError({
                'specialities': 'Add at least one speciality for this doctor.'
            })

        schedule = self.initial_data.get('working_hours')
        if schedule is None:
            return attrs

        if not isinstance(schedule, list) or not schedule:
            raise serializers.ValidationError({
                'working_hours': 'Add at least one working day and its hours.'
            })

        schedule_serializer = DoctorScheduleItemSerializer(data=schedule, many=True)
        schedule_serializer.is_valid(raise_exception=True)
        attrs['working_hours'] = schedule_serializer.validated_data
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        schedule = validated_data.pop('working_hours', [])
        specialities = validated_data.pop('Specialities', [])
        doctor = Doctor.objects.create(**validated_data)
        doctor.Specialities.set(specialities)
        DoctorWorkingHours.objects.bulk_create(
            [DoctorWorkingHours(doctor=doctor, **item) for item in schedule]
        )
        return doctor

    @transaction.atomic
    def update(self, instance, validated_data):
        schedule = validated_data.pop('working_hours', None)
        specialities = validated_data.pop('Specialities', None)
        doctor = super().update(instance, validated_data)
        if specialities is not None:
            if not specialities:
                raise serializers.ValidationError({
                    'specialities': 'Add at least one speciality for this doctor.'
                })
            doctor.Specialities.set(specialities)
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
        if 'start_time' not in attrs or 'end_time' not in attrs:
            raise serializers.ValidationError(
                'A working day must include both start and end times.'
            )
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
        if 'start_time' not in attrs or 'end_time' not in attrs:
            raise serializers.ValidationError(
                'A working day must include both start and end times.'
            )
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError(
                {'end_time': 'End time must be later than start time.'}
            )
        return attrs


class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = ['id', 'speciality_name', 'speciality_description']

    def validate_speciality_name(self, value):
        if Speciality.objects.filter(speciality_name__iexact=value).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists():
            raise serializers.ValidationError('This speciality already exists.')
        return value


class ClinicalServiceSerializer(serializers.ModelSerializer):
    speciality_name = serializers.CharField(
        source='speciality.speciality_name', read_only=True
    )

    class Meta:
        model = ClinicalService
        fields = [
            'id', 'service_name', 'speciality', 'speciality_name',
            'service_description',
        ]

class BookAppointmentSerializer(serializers.Serializer):
    full_name=serializers.CharField(max_length=200)
    email=serializers.EmailField()
    phone_number=serializers.CharField(max_length=20)
    address=serializers.CharField()

    clinical_service = serializers.PrimaryKeyRelatedField(
        queryset=ClinicalService.objects.select_related('speciality')
    )
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
        clinical_service = attrs['clinical_service']
        if not doctor.Specialities.filter(pk=clinical_service.speciality_id).exists():
            raise serializers.ValidationError({
                'doctor_name': 'This doctor does not provide the selected service.'
            })

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
        clinical_service = validated_data.pop('clinical_service')

        try:
            appointment = create_appointment(
                doctor=doctor,
                clinical_service=clinical_service,
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
    service_name = serializers.CharField(
        source='clinical_service.service_name', read_only=True
    )
    
    class Meta:
        model = Appointment
        fields = [
            'patient_name', 'doctor_name', 'service_name', 'appointment_date',
            'appointment_time', 'additional_information', 'cancelled_at',
            'cancellation_reason', 'is_rescheduled', 'created_at',
        ]




# serializer that makes doctors name readable and gives appoinment booking response cleaner
class AppointmentResponseSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    service_name = serializers.CharField(
        source='clinical_service.service_name', read_only=True
    )
    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_date', 'appointment_time', 'doctor_name',
            'service_name', 'is_rescheduled', 'cancelled_at',
        ]

class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5, error_messages={
        "required":"You must provide a cancellation reason",
        "blank":"Cancellation reason cannot be empty"
    })

class RescheduleAppointmentSerializer(serializers.Serializer):
    appointment_date = serializers.DateField(required=True)
    appointment_time = serializers.TimeField(required=True)
    doctor_name = serializers.CharField(required=False)

    def validate_doctor_name(self, value):
        doctor = Doctor.objects.filter(full_name__iexact=value, is_active=True).first()
        if not doctor:
            raise serializers.ValidationError('Active doctor with this name does not exist')
        return doctor

    def update(self, instance, validated_data):
        try:
            return reschedule_appointment(
                appointment=instance,
                new_date=validated_data['appointment_date'],
                new_time=validated_data['appointment_time'],
                doctor=validated_data.get('doctor_name'),
            )
        except BookingError as e:
            raise serializers.ValidationError(str(e))