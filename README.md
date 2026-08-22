# Clinical Booking System 
## Overview
This project is a backend clinical system designed to allow patients to book appointments by selecting an available clinical service, date and 30min time slot

The system does not require patients to select or wait for a doctor to confirm their appointment. Instead, doctor assignment happens automatically behind the scenes based on: 

- The clinical service requested and its required speciality. 
- The doctor's working hours. 
- Existing appointment and availability
- Previous doctor-patient relationship
- Doctor rotation

The core principle is 
**The patient chooses the service and the available time, the system chooses the doctor**

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
2. Doctor Assignment

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
Stores doctors who can be assigned to appointments. A doctor can have multiple specialities. 

Working hours are stired separately because schedules can differ by day. 
```text
 full_name
 email
 phone_number
 specialties
 is_active
```

### 3. Speciality
Represents a doctor's area of expertise and are shared by doctors and clinical services. 

This allows the system to determine which doctors are qualified for a service without relying on text matching. 
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
```text
 doctor
 weekday
 start_time
 end_time
```
### 6. Appointment
Represents a successfully booked appointment. Considering every appointment is exactly *30 min*. 

## Availability
Availability is calculated dynamically rather than stores as a separate field. 

The calendar requests available slots using:
```text
Clinical Service
+
Date
```
The availability sevice then:
```text
1. Find the specialty required by the service.
2. Find doctors with that specialty.
3. Check their working hours.
4. Check existing appointments.
5. Generate 30-minute slots.
6. Remove slots where all eligible doctors are booked.
7. Remove slots less than one hour from the current time.
8. Return the remaining slots.
```
A slot is displayed only when at least one suitable doctor can handle it. 

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
The rule is applied when generating available slots and cheched again when creating appointment so it cannot be bypassed through a direct `Get/Appointments` API request. 

## Doctor Assignment
The patient never selects a doctor. Doctor selection happens entirely in the backend. The assignment process is: 
```text
Clinical Service
        ↓
Required Specialty
        ↓
Eligible Doctors
        ↓
Working Hours
        ↓
Existing Appointments
        ↓
Previous Doctor Preference
        ↓
Rotation
        ↓
Assign Doctor
```

### Assignment rules
**1. Match the service**

The doctor must have the specialty required by the selected clinical service.

**2. Check working hours**

The doctor must be working during the selected 30-minute slot.

**3. Check existing appointments**

A doctor cannot be assigned to an occupied slot.

**4. Prefer the previous doctor**

If the patient has previously seen an eligible doctor and that doctor is available, the system prioritizes them.

This provides continuity of care.

**5. Apply rotation**

If the previous doctor is unavailable, the system selects from the remaining eligible doctors using a rotation strategy, prioritizing the doctor who has gone the longest since their last assignment.

## Prevent Double booking
Availability shown on the calendar is not considered sufficient on its own. 

When the patient submits a booking, the backend checks availability again inside a database transaction. 

This is to prevent a scenario where only one doctor is available and two patients are booking at the same time. So the database: 
```text
Start transaction
      ↓
Re-check slot
      ↓
Find eligible doctor
      ↓
Assign doctor
      ↓
Create appointment
      ↓
Commit
```
The appointment model also uses a database-level constraint preventing the same doctor from being assigned to the same sate and time more than once. 

## Booking Flow
```text
Patient enters details
        ↓
Selects clinical service
        ↓
Selects date
        ↓
Calendar requests available slots
        ↓
Availability service calculates slots
        ↓
Patient selects a slot
        ↓
Booking request submitted
        ↓
Backend re-checks availability
        ↓
Doctor assignment service selects doctor
        ↓
Appointment created
```

The booking form contains:
```text
Full name
Email
Phone number
Address
Appointment date
Appointment time
Clinical service
Additional information
```

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
    ├── availability.py
    └── doctor_assignment.py
```

### `models.py`
Defines database models, relationship and constraints. 

### `serializers.py`
Validates incoming booking data and serializes API responses.

### `views.py`
Handles API requests and delegates scheduling logic to the service layer.

### `availability.py`
Calculates available 30-minute appointment slots.

### `doctor_assignment.py`
Selects and assigns the most suitable available doctor.


## Key Design Decisions and Trade-Offs

### Separatae Working hours from Doctor
`DoctorWorkingHour` is a separate model that makes different scedules easy to represent and keeps the doctor model simple. 

### Dynamic availabilit instead of stored slots. 
Calculating available slots from working hours and existing appointments helps avoid maintaining a separate slot table and keeps availability consistent with the current database state. 

### Doctor selected by the backend. 
Patients select a service and available time and not a doctor. This prevents patient from selecting unavaibale, unsuitable doctors or incase the patient is new and has no info about the doctors available.Instead allow the system to enforce speciality, availability, continuity and rotation rules consistently. 

### Previous doctor vs rotation
Check on previous eligible doctor, then apply rotation to balance continuity of care with fair distribution of appointments. 

## Future consideration: Multiple clinical centers
The current MVP intentionally does not include a `clinicalCenter` model. 

The assessment starts with a small five-doctor setup, so adding location-based scheduling would introduce complexity that is not required for the current scenario. 

If the system later expands to multiple clinical branches, `clinicalCenter` can be introduced and connected to doctor schedule and appointments.

This keeps the current implementation focused while leaving room for future expansion. 

## 12. Summary

The system is built around a simple scheduling principle:

**Patients choose what service they need and when they are available; the backend determines which doctor should provide the service.**

The system uses:

```text
Django Models
      ↓
Availability Service
      ↓
Doctor Assignment Service
      ↓
Appointment
```

This design keeps the MVP simple while supporting dynamic availability, automatic doctor assignment, continuity of care, fair doctor rotation, and protection against double booking.