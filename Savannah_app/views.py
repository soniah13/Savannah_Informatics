from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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

