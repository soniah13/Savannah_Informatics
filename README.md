# Clinical Booking System 

## Deployment & Pipeline


- **Deployment branch:** `main`
- **CI/CD pipeline:** Every push to `main` triggers the pipeline. It sets up Python 3.14, installs dependencies from `requirements.txt`, runs database migrations, and executes the automated test suite. After the checks pass, the latest code is deployed to the production environment.

## Overview
This project is a backend clinical system designed to allow patients to book appointments by selecting a doctor, clinical service, date and 30min time slot.  

The patient selects the doctor they want to see, and depending on the selected doctor and appointment date, the system dynamically generates the available 30-minute time slots based on the doctor's working hours and existing appointments.  

The core principle is  
**The patient chooses the doctor, service, date and available time, while the system validates the appointment against the doctor's schedule and existing appointments.** 

## System Design
The system separates data from scheduling logic. 

### Django Models
1. Patient
2. Doctor
3. Speciality
4. Clinical Service
5. Doctor Working Hours(Shift)
6. Appointment

### Services
1. Doctor Availability

`models.py` manages data and relationships, while the services handles availability and doctor assignment.

## Models
### 1. Patient
Stores Patient Information. Keeping in mind that A patient can have multiple appointment. 

Patients Information is stored once and referenced by appointment rather than duplicated in each appointment. 
```text
 full_name
 email
 phone_number
 address
```

### 2. Doctor
Stores doctors who can be selected by patients when booking an appointment. A doctor can have multiple specialities.  
 
Working hours are stored separately because schedules can differ by day.  
```text
 full_name
 email
 phone_number
 specialties
 is_active
```

### 3. Speciality
Represents a doctor's area of expertise and are shared by doctors and clinical services. 

```text
Specialty
   ├── Doctors
   └── Clinical Services
```
### 4. Clinical Service
Represents the service the patient wants to book. Each service maps to a required speciality.

This relationship is used to identify eligible doctors automatically. 

```text
 name
 specialty
 description
```

### 5. Doctor Working Hours
Defines when a doctor is available to work. Considering doctors work in shifts.  
 
Working hours are stored separately from `Doctor` so different schedules can be represented without complicating the doctor model.  

When creating a doctor, the available working days and the working hours for each day can be provided. A validation constraint ensures that no selected working day exists without corresponding working hours. 
```text
 doctor
 weekday
 start_time
 end_time
```
### 6. Appointment
Represents a successfully booked appointment. Considering every appointment is exactly *30 min*.  
 
The appointment is linked to the selected doctor, clinical service, date and time.  

## Availability
Availability is calculated dynamically rather than stores as a separate field. 

The calendar requests available slots using:
```text
Doctor
+
Date
```
The availability sevice then:
```text
1. Find the selected doctor's working hours for the requested day. 
2. Check existing appointments for the selected doctor. 
3. Generate 30-minute slots based on the doctor's working hours. 
4. Remove slots that are already booked. 
5. Remove slots less than one hour from the current time. 
6. Return the remaining slots. 
```
A slot is displayed only when the selected doctor is available at that time. 

### Dynamic Availability
The system does not need to reload or restart when a booking is made. Availability is derived from the current database state by checking:
```text
Doctor Working Hours
        +
Existing Appointments
        =
Current Available Slots
```
After an appointment is created, the next availability request automatically reflects the updated schedule. 

### One-Hour Booking Rule
Patients cannot book an appointment less than one hour in advance.  

The rule is applied when generating available slots and checked again when creating an appointment so it cannot be bypassed through a direct API request. 

## Prevent Double booking 
Availability shown on the calendar is not considered sufficient on its own.  
 
When the patient submits a booking, the backend checks availability again inside a database transaction.  
 
This is to prevent a scenario where the same doctor and time slot are selected by two patients at the same time. So the database:  
```text 
Start transaction 
      ↓ 
Re-check slot 
      ↓ 
Verify doctor availability 
      ↓ 
Create appointment 
      ↓ 
Commit 
``` 

The appointment model also uses a database-level constraint preventing the same doctor from being assigned to the same date and time more than once.  
 
## Booking Flow 
```text 
Patient enters details 
        ↓ 
Selects doctor 
        ↓ 
Selects clinical service 
        ↓ 
Selects date 
        ↓ 
Calendar requests available slots for selected doctor and date 
        ↓ 
Availability service calculates slots 
        ↓ 
Patient selects a slot 
        ↓ 
Booking request submitted 
        ↓ 
Backend re-checks availability 
        ↓ 
Appointment created 
``` 
 
The booking form contains: 
```text 
Full name 
Email 
Phone number 
Address 
Doctor 
Appointment date 
Appointment time 
Clinical service 
Additional information 
``` 
 
## API Endpoints 

The system provides endpoints for managing doctors, working schedules, availability and appointments.  

These include:  
```text 
Base URL: /api/v1/

POST /doctors/
- Create a doctor with available working days and working hours

GET /appointments/
- Retrieve all appointments

GET /doctors/{id}/availability/?date=YYYY-MM-DD
- Retrieve available 30-minute times for a selected doctor and date

The API also exposes patient and working-hours resources through the same
versioned base URL.
``` 

When creating a doctor, the request includes the doctor's available working days and the working hours for each selected day. The system validates the schedule to ensure that no working day is configured without working hours.  

## Testing Frontend 

A testing frontend template was added to test the API endpoints through a user-facing booking flow.  

The frontend makes it possible to test the endpoints in a more practical way and evaluate the complete user experience instead of testing each endpoint independently.  

The testing flow allows the user to:  
```text 
Select doctor 
        ↓ 
Select date 
        ↓ 
View dynamically generated available times 
        ↓ 
Select appointment time 
        ↓ 
Create appointment 
        ↓ 
View appointments 
``` 

The frontend testing experience also informed the design decisions by making it easier to identify a smoother and more intuitive booking flow.  

## Components 
```text 
appointments/ 
│ 
├── models.py 
├── serializers.py 
├── views.py 
├── urls.py 
│ 
└── services/ 
    └── availability.py 
``` 
 
### `models.py` 
Defines database models, relationship and constraints.  
 
### `serializers.py` 
Validates incoming booking data and serializes API responses. 
 
### `views.py` 
Handles API requests and delegates availability and booking logic to the service layer. 
 
### `availability.py` 
Calculates available 30-minute appointment slots based on the selected doctor, working hours and existing appointments. 
 
 
## Key Design Decisions and Trade-Offs 
 
### Separate Working hours from Doctor 
`DoctorWorkingHour` is a separate model that makes different schedules easy to represent and keeps the doctor model simple.  

Working days and their corresponding working hours are configured when creating a doctor, with validation to ensure that every working day has working hours.  
 
### Dynamic availability instead of stored slots.  
Calculating available slots from working hours and existing appointments helps avoid maintaining a separate slot table and keeps availability consistent with the current database state.  
 
### Doctor selected by the patient.  
Patients select the doctor they want to see, together with the clinical service and appointment date. The available appointment times are then generated based on that doctor's working hours and existing appointments.  

This provides a more direct and transparent booking experience while the backend still validates that the selected doctor is available for the requested time.  
 
### Testing through a frontend 
A frontend testing template was added to test the endpoints through an actual booking flow.  

This made it easier to test the interaction between the endpoints, verify the availability flow and make design decisions based on a smoother user experience rather than testing the endpoints only in isolation.  
 
## Future consideration: Multiple clinical centers 
The current MVP intentionally does not include a `clinicalCenter` model.  
 
The assessment starts with a small five-doctor setup, so adding location-based scheduling would introduce complexity that is not required for the current scenario.  
 
If the system later expands to multiple clinical branches, `clinicalCenter` can be introduced and connected to doctor schedule and appointments. 
 
This keeps the current implementation focused while leaving room for future expansion.  
 
## Summary 
 
The system is built around a simple scheduling principle: 
 
**Patients choose the doctor and service they need, select a date, and the system generates the available appointment times based on the doctor's working schedule and existing appointments.** 
 
The system uses: 
 
```text 
Django Models 
      ↓ 
Doctor Working Hours 
      ↓ 
Availability Service 
      ↓ 
Appointment 
``` 
 
This design keeps the MVP simple while supporting dynamic availability, patient-selected doctors, configurable doctor working schedules, appointment management, protection against double booking, and a testing frontend for validating the API and user experience.