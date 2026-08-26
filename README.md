# Clinical Booking System

## Deployment & Pipeline
- **Deployed Link:** `https://savannah-informatics-mu5p.onrender.com/`
- **Deployment Branch:** The `main` branch triggers the deployment automatically upon a successful merge or push.
- **CI/CD Pipeline:** The pipeline automatically runs on every push to `main`. It sets up the Python environment (Python 3.14), installs dependencies via `requirements.txt`, runs database migrations, and executes the automated test suite to ensure no breaking changes are introduced. Once tests pass, the pipeline deploys the latest code to the production environment.

## Overview

This project is a backend clinical system designed to allow patients to book appointments seamlessly. To provide the best user experience, the system empowers the patient to choose their preferred doctor and appointment date.

The core principle is: **The patient chooses the doctor and the date; the system dynamically generates the available time slots based on that specific doctor's working hours and existing appointments.**

## System Design

The system separates data from scheduling logic and includes a testing frontend template to ensure a smooth user experience.

### Django Models

1. **Patient:** Stores patient information (Full name, email, phone number, address).
2. **Doctor:** Stores doctors who can be assigned to appointments.
3. **Speciality:** Represents a doctor's area of expertise.
4. **Clinical Service:** Represents the service the patient wants to book.
5. **Doctor Working Hours (Shift):** Defines when a doctor is available to work. Includes constraints to ensure no working day is created without corresponding working hours.
6. **Appointment:** Represents a successfully booked 30-minute appointment.

## Availability

Availability is calculated dynamically based on the specific doctor selected by the patient.

The calendar requests available slots using:

`Doctor` + `Date`

The availability service then:

1. Checks the specific doctor's working days and hours for the chosen date.
2. Checks the doctor's existing appointments.
3. Generates 30-minute slots.
4. Removes slots that are already booked.
5. Removes slots less than one hour from the current time.
6. Returns the remaining available slots for the patient to choose from.

## Doctor Assignment 
Unlike automated assignment, the patient explicitly selects their doctor.

1. The booking form presents a list of available doctors.
2. The patient selects a doctor and a date.
3. The system generates available times depending on that exact doctor's schedule.

## Prevent Double Booking

Availability shown on the calendar is not considered sufficient on its own. When the patient submits a booking, the backend checks availability again inside a database transaction:

`Start transaction` → `Re-check slot` → `Create appointment` → `Commit`

## Booking Flow

1.`Patient enters details` 

2.`Selects preferred Doctor` 

3.`Selects Date`

4.`System fetches available slots for that Doctor on that Date`

5.`Patient selects a 30-min time slot`

6.`Booking request submitted & Backend re-checks availability`

7.`Appointment created`

## Components & Endpoints

- **`models.py`:** Defines database models, relationships, and constraints.
- **`serializers.py`:** Validates incoming booking data and serializes API responses.
- **`views.py`:** Handles API requests. Key endpoints include:
  - `GET /appointments/`: Retrieves all appointments in the system.
  - `POST /doctors/`: Creates a doctor. Requires selecting available working days and specifying working hours for each day.
- **`availability.py`:** Calculates available 30-minute appointment slots for the selected doctor.
- **Frontend Testing Template:** A lightweight UI added to smoothly test endpoints, validate the booking flow, and ensure an optimal user experience.

## Key Design Decisions and Trade-Offs

- **Patient-Selected Doctor:**
  - *Decision:* Changed from automated backend assignment to allowing the patient to select the doctor's name directly on the form.
  - *Trade-off:* While this might lead to uneven distribution of appointments among doctors (favoring popular doctors), it significantly improves patient autonomy, satisfaction, and the overall user experience.

- **Dynamic Availability by Doctor & Date:**
  - *Decision:* Time slots are only generated *after* a doctor and date are selected.
  - *Trade-off:* Requires an extra API call during the form-filling process, but guarantees that the slots shown are 100% accurate to that specific doctor's daily shift.

- **Strict Working Hours Constraints:**
  - *Decision:* Added strict validation when creating a doctor to ensure working days cannot be saved without explicitly defined working hours.
  - *Trade-off:* Makes the doctor creation payload slightly more complex, but entirely prevents edge-case errors where a doctor appears available on a day but has no bookable slots.

- **Frontend Testing Template:**
  - *Decision:* Included a frontend template alongside the backend API.
  - *Trade-off:* Adds minor overhead to a strictly backend repository, but is invaluable for immediate visual endpoint testing and UX validation.

## **Future Considerations**

If the system later expands to multiple clinical branches, a `ClinicalCenter` model can be introduced and connected to doctor schedules and appointments.


## **AI Reflection**

### 1. What did you use AI for across the four sections?

- **System Design:** Used AI for brainstorming and reviewing models, relationships, and design decisions. Initially, I designed automatic doctor assignment, but after reviewing the assessment requirements, I changed the system so patients select a doctor. AI helped me restructure the existing code to support this change.

- **API Implementation:** Used AI as a second pair of eyes to identify syntax errors, missing logic, improve existing code, and verify that the required endpoints were implemented.

- **Deployment & CI/CD:** Used AI mainly for debugging deployment/configuration errors and making last-minute improvements within the assessment timeframe.

- **Testing:** Used AI to help structure Django tests and create a simple template for manually testing the API endpoints.

I treated AI as a development assistant and reviewed its suggestions against the requirements before implementing them.

### 2. Give one example where an AI suggestion improved your work. What did you prompt it with?

AI suggested separating my appointment business logic from the Django views into a `services/` layer. This made the booking, availability, cancellation, rescheduling, and working-hours logic easier to maintain and test.

**Prompt:**

> "I am building a Clinical Appointment Booking API using Django REST Framework. How can I separate my business logic from my views and serializers and structure services for appointment booking, availability, cancellation, rescheduling, and working hours?"

I adapted the suggestion to fit my existing project rather than copying the implementation directly.

### 3. Give one example where AI output was wrong or incomplete and how you caught it.

AI suggested adding a `status` field to the `Appointment` model.

I rejected this after comparing it with my requirements. In my system, an appointment is immediately considered booked once successfully created, so a separate `pending` or `confirmed` status was unnecessary and would add complexity.

This reinforced the importance of validating AI suggestions against the actual requirements.

### 4. Name two decisions you made without AI. Why did you trust your own judgment?

**Decision 1: Patient selects the doctor**

I decided that the booking form should allow patients to view and select an available doctor. This aligns with the assessment requirement and provides a clearer booking experience for the patient.

**Decision 2: Doctor working hours determine available slots**

I decided that doctors must specify both their working days and the actual time ranges they work. When a patient selects a doctor and date, the system automatically generates the available 30-minute slots based on the doctor's working hours and existing appointments.

I trusted these decisions because I was considering both the assessment requirements and the actual user experience, rather than simply implementing the easiest technical solution.

### Overall Reflection

AI helped me work faster with debugging, testing, restructuring, and implementation. However, I remained responsible for the final architecture and decisions. I learned that AI suggestions are most useful when treated as guidance to evaluate, not as requirements to follow blindly.