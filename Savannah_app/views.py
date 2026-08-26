from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .exceptions import BookingError
from .models import (
    Appointment,
    ClinicalService,
    Doctor,
    DoctorWorkingHours,
    Patient,
    Speciality,
)
from .serializers import (
    AppointmentListSerializer,
    AppointmentResponseSerializer,
    BookAppointmentSerializer,
    CancelAppointmentSerializer,
    ClinicalServiceSerializer,
    DoctorSerializer,
    DoctorWorkingHoursSerializer,
    PatientSerializer,
    RescheduleAppointmentSerializer,
    SpecialitySerializer,
)
from .services.availability import get_doctor_available_slots
from .services.bookings import cancel_appointment


class AppointmentViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(
            AppointmentResponseSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )

    def list(self, request):
        appointments = Appointment.objects.all().order_by(
            '-appointment_date', '-appointment_time'
        )
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            appointment = cancel_appointment(
                appointment, serializer.validated_data['reason']
            )
        except BookingError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppointmentResponseSerializer(appointment).data)

    @action(detail=True, methods=['patch'])
    def reschedule(self, request, pk=None):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = RescheduleAppointmentSerializer(
            appointment, data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            appointment = serializer.save()
        except BookingError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppointmentResponseSerializer(appointment).data)


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    queryset = Doctor.objects.all().order_by('full_name')

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        doctor = get_object_or_404(Doctor, pk=pk, is_active=True)
        date_str = request.query_params.get('date')

        if not date_str:
            return Response(
                {'error': 'Please provide a ?date=YYYY-MM-DD query parameter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'doctor': doctor.full_name,
            'date': query_date,
            'available_slots': [
                slot.strftime('%H:%M')
                for slot in get_doctor_available_slots(doctor, query_date)
            ],
        })


class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Patient.objects.all().order_by('full_name')
    serializer_class = PatientSerializer


class SpecialityViewSet(viewsets.ModelViewSet):
    queryset = Speciality.objects.all().order_by('speciality_name')
    serializer_class = SpecialitySerializer


class ClinicalServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClinicalService.objects.select_related('speciality').all().order_by(
        'service_name'
    )
    serializer_class = ClinicalServiceSerializer


class DoctorWorkingHoursViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorWorkingHoursSerializer
    queryset = DoctorWorkingHours.objects.select_related('doctor').order_by(
        'doctor__full_name', 'weekday', 'start_time'
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset