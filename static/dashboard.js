const api = '/api/v1';
const $ = (selector) => document.querySelector(selector);

function csrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function formData(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function showResult(selector, value, success = true) {
    const target = $(selector);
    target.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    target.classList.toggle('success', success);
    target.classList.toggle('error', !success);
}

async function request(path, options = {}) {
    const response = await fetch(`${api}${path}`, {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken(),
            ...(options.headers || {}),
        },
        ...options,
    });
    const text = await response.text();
    let data;
    try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
    if (!response.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
    return data;
}

function notify(message) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2600);
}

async function loadAppointments() {
    const body = $('#appointments-body');
    try {
        const appointments = await request('/appointments/');
        body.innerHTML = appointments.length ? appointments.map((appointment) => {
            const cancelled = Boolean(appointment.cancelled_at);
            return `<tr><td>${appointment.patient_name}</td><td>${appointment.doctor_name}</td><td>${appointment.appointment_date}</td><td>${appointment.appointment_time.slice(0, 5)}</td><td><span class="badge ${cancelled ? 'cancelled' : ''}">${cancelled ? 'Cancelled' : 'Booked'}</span></td><td>${appointment.additional_information || '-'}</td></tr>`;
        }).join('') : '<tr><td colspan="6" class="empty">No appointments found.</td></tr>';
        $('#connection-status').innerHTML = '<span></span>Connected';
    } catch (error) {
        body.innerHTML = `<tr><td colspan="6" class="empty">${error.message}</td></tr>`;
        $('#connection-status').innerHTML = '<span></span>API unavailable';
    }
}

async function loadPatients() {
    try {
        const patients = await request('/patients/');
        showResult('#patients-result', patients.length ? patients.map((patient) => `${patient.full_name}  |  ${patient.email}\n${patient.phone_number}  |  ${patient.address}`).join('\n\n') : 'No patients found.');
    } catch (error) { showResult('#patients-result', error.message, false); }
}

async function loadDoctors() {
    const selects = [$('#availability-doctor'), $('#booking-doctor')];
    try {
        const doctors = await request('/doctors/');
        doctors.forEach((doctor) => selects.forEach((select) => {
            const option = document.createElement('option');
            option.value = doctor.full_name;
            option.dataset.doctorId = doctor.id;
            option.textContent = doctor.full_name;
            select.appendChild(option);
        }));
        doctors.forEach((doctor) => {
            const option = $('#availability-doctor').querySelector(`[data-doctor-id="${doctor.id}"]`);
            if (option) option.value = doctor.id;
        });
    } catch (error) {
        showResult('#booking-slots', error.message, false);
    }
}

async function loadBookingSlots() {
    const doctorOption = $('#booking-doctor').selectedOptions[0];
    const date = $('#booking-date').value;
    const timeSelect = $('#booking-time');
    timeSelect.innerHTML = '<option value="">Loading available times...</option>';
    timeSelect.disabled = true;
    if (!doctorOption?.dataset.doctorId || !date) {
        timeSelect.innerHTML = '<option value="">Choose doctor and date first</option>';
        showResult('#booking-slots', 'Select a doctor and date to see available times.');
        return;
    }
    try {
        const data = await request(`/doctors/${doctorOption.dataset.doctorId}/availability/?date=${date}`);
        timeSelect.innerHTML = data.available_slots.length
            ? '<option value="">Choose an available time</option>' + data.available_slots.map((slot) => `<option value="${slot}">${slot}</option>`).join('')
            : '<option value="">No available times</option>';
        timeSelect.disabled = !data.available_slots.length;
        showResult('#booking-slots', data.available_slots.length ? `${data.available_slots.length} available time(s) for ${data.doctor} on ${data.date}.` : 'No available times for this doctor and date.');
    } catch (error) {
        timeSelect.innerHTML = '<option value="">Availability unavailable</option>';
        showResult('#booking-slots', error.message, false);
    }
}

$('#availability-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = formData(event.currentTarget);
    try { showResult('#availability-result', await request(`/doctors/${data.doctor_id}/availability/?date=${data.date}`)); }
    catch (error) { showResult('#availability-result', error.message, false); }
});

$('#booking-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = formData(event.currentTarget);
    const doctorOption = $('#booking-doctor').selectedOptions[0];
    if (!doctorOption?.dataset.doctorId || !data.appointment_time) {
        showResult('#booking-result', 'Choose a doctor, date, and available time first.', false);
        return;
    }
    try { showResult('#booking-result', await request('/appointments/', { method: 'POST', body: JSON.stringify(data) })); notify('Appointment booked'); loadAppointments(); loadPatients(); }
    catch (error) { showResult('#booking-result', error.message, false); }
});

$('#booking-doctor').addEventListener('change', loadBookingSlots);
$('#booking-date').addEventListener('change', loadBookingSlots);

$('#reschedule-button').addEventListener('click', async () => {
    const data = formData($('#manage-form'));
    if (!data.appointment_id || !data.reschedule_date || !data.reschedule_time) return showResult('#manage-result', 'Appointment ID, date, and time are required.', false);
    try { showResult('#manage-result', await request(`/appointments/${data.appointment_id}/reschedule/`, { method: 'PATCH', body: JSON.stringify({ appointment_date: data.reschedule_date, appointment_time: data.reschedule_time }) })); notify('Appointment rescheduled'); loadAppointments(); }
    catch (error) { showResult('#manage-result', error.message, false); }
});

$('#cancel-button').addEventListener('click', async () => {
    const data = formData($('#manage-form'));
    if (!data.appointment_id || !data.reason) return showResult('#manage-result', 'Appointment ID and a cancellation reason are required.', false);
    try { showResult('#manage-result', await request(`/appointments/${data.appointment_id}/cancel/`, { method: 'PATCH', body: JSON.stringify({ reason: data.reason }) })); notify('Appointment cancelled'); loadAppointments(); }
    catch (error) { showResult('#manage-result', error.message, false); }
});

$('#refresh-appointments').addEventListener('click', loadAppointments);
$('#refresh-patients').addEventListener('click', loadPatients);
loadAppointments();
loadPatients();
loadDoctors();
