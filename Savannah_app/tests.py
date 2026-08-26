from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Appointment, Doctor, DoctorWorkingHours


class AppointmentEndpointTests(APITestCase):
	def setUp(self):
		self.doctor = Doctor.objects.create(
			full_name='Dr. Ada Lovelace',
			email='ada@example.com',
			phone_number='1234567890',
		)
		DoctorWorkingHours.objects.create(
			doctor=self.doctor,
			weekday=(timezone.localdate() + timedelta(days=2)).weekday(),
			start_time='09:00',
			end_time='12:00',
		)
		self.appointment_date = timezone.localdate() + timedelta(days=2)
		self.booking_data = {
			'full_name': 'Grace Hopper',
			'email': 'grace@example.com',
			'phone_number': '0987654321',
			'address': '1 Navy Street',
			'doctor_name': self.doctor.full_name,
			'appointment_date': self.appointment_date,
			'appointment_time': '09:00',
		}

	def book_appointment(self):
		return self.client.post(
			reverse('appointment-list'), self.booking_data, format='json'
		)

	def test_can_book_and_list_appointments_and_patients(self):
		response = self.book_appointment()

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(
			self.client.get(reverse('appointment-list')).status_code,
			status.HTTP_200_OK,
		)
		patients_response = self.client.get(reverse('patient-list'))
		self.assertEqual(patients_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(patients_response.data), 1)

	def test_availability_excludes_booked_slot_and_cancel_releases_it(self):
		self.book_appointment()
		availability_url = reverse(
			'doctor-availability', kwargs={'pk': self.doctor.pk}
		)
		availability = self.client.get(
			availability_url, {'date': self.appointment_date}
		)
		self.assertNotIn('09:00', availability.data['available_slots'])

		appointment = Appointment.objects.get()
		cancel_response = self.client.patch(
			reverse('appointment-cancel', kwargs={'pk': appointment.pk}),
			{'reason': 'No longer available'},
			format='json',
		)
		self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
		availability = self.client.get(
			availability_url, {'date': self.appointment_date}
		)
		self.assertIn('09:00', availability.data['available_slots'])

	def test_reschedule_releases_original_slot(self):
		self.book_appointment()
		appointment = Appointment.objects.get()
		response = self.client.patch(
			reverse('appointment-reschedule', kwargs={'pk': appointment.pk}),
			{
				'appointment_date': self.appointment_date,
				'appointment_time': '10:00',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		appointment.refresh_from_db()
		self.assertEqual(str(appointment.appointment_time), '10:00:00')

	def test_doctor_can_be_created_with_working_schedule(self):
		response = self.client.post(
			reverse('doctor-list'),
			{
				'full_name': 'Dr. Marie Curie',
				'email': 'marie@example.com',
				'phone_number': '1112223333',
				'working_hours': [
					{'weekday': 1, 'start_time': '08:00', 'end_time': '12:00'}
				],
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['working_hours'][0]['weekday'], 1)

	def test_doctor_schedule_requires_a_working_day(self):
		data = {
			'full_name': 'Dr. No Schedule',
			'email': 'none@example.com',
			'phone_number': '1112223333',
			'working_hours': [],
		}
		response = self.client.post(reverse('doctor-list'), data, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('working_hours', response.data)

	def test_working_hours_requires_both_times(self):
		response = self.client.post(
			reverse('working-hours-list'),
			{'doctor': self.doctor.pk, 'weekday': 1, 'start_time': '09:00'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('end_time', response.data)
