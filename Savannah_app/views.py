from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .models import Doctor
from .services.availability import DoctorWorkingHours, generate_slots, is_bookable_time, doctor_has_conflicts
from django.shortcuts import get_object_or_404
from .serializers import BookAppointmentSerializer, AppointmentResponseSerializer

# Create your views here.
class BookAppointmentView(APIView):
    def post(self, request):
        serializer = BookAppointmentSerializer(data=request.data)
        if serializer.is_valid():
            appoitnment = serializer.save()
            response_data = AppointmentResponseSerializer(appoitnment).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorAvailabilityView(APIView):
    def get(self, request, pk):
        doctor = get_object_or_404(Doctor, id=pk, is_active=True)
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({'error':"Please provide a ?date=YYYY-MM-DD query parameter."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error":"Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        weekday = query_date.weekday()
        working_hours = DoctorWorkingHours.objects.filter(doctor=doctor, weekday=weekday)

        available_slots = []
        for work_hour in working_hours:
            slots = generate_slots(work_hour.start_time, work_hour.end_time)
            for slot in slots:
                if is_bookable_time(query_date, slot) and not doctor_has_conflicts(doctor, query_date, slot):
                    available_slots.append(slot.strftime("%H:%M"))

            return Response({
                "doctor": doctor.full_name,
                "date": query_date,
                "available_slots": sorted(available_slots)
            }, status=status.HTTP_200_OK)