const api = '/api/v1';
const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const $ = (selector) => document.querySelector(selector);

function csrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function showResult(value, success = true) {
    const target = $('#doctor-result');
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

function buildSchedule(schedule = []) {
    const byDay = Object.fromEntries(schedule.map((item) => [item.weekday, item]));
    $('#schedule-rows').innerHTML = weekdays.map((day, weekday) => {
        const item = byDay[weekday] || {};
        return `<div class="schedule-row">
            <label class="check-label"><input type="checkbox" data-weekday="${weekday}" ${item.start_time ? 'checked' : ''}> ${day}</label>
            <input type="time" data-start="${weekday}" value="${(item.start_time || '').slice(0, 5)}" ${item.start_time ? '' : 'disabled'} aria-label="${day} start time">
            <span>to</span>
            <input type="time" data-end="${weekday}" value="${(item.end_time || '').slice(0, 5)}" ${item.end_time ? '' : 'disabled'} aria-label="${day} end time">
        </div>`;
    }).join('');
}

function validateScheduleRows() {
    for (const checkbox of document.querySelectorAll('[data-weekday]')) {
        if (!checkbox.checked) continue;
        const weekday = checkbox.dataset.weekday;
        const start = document.querySelector(`[data-start="${weekday}"]`);
        const end = document.querySelector(`[data-end="${weekday}"]`);
        if (!start.value || !end.value) {
            showResult(`Select both start and end times for ${weekdays[weekday]}.`, false);
            return false;
        }
    }
    if (!document.querySelector('[data-weekday]:checked')) {
        showResult('Select at least one working day and add its hours.', false);
        return false;
    }
    return true;
}

function readSchedule() {
    return weekdays.flatMap((_, weekday) => {
        const enabled = document.querySelector(`[data-weekday="${weekday}"]`).checked;
        const start = document.querySelector(`[data-start="${weekday}"]`).value;
        const end = document.querySelector(`[data-end="${weekday}"]`).value;
        return enabled ? [{ weekday, start_time: start, end_time: end }] : [];
    });
}

function resetForm() {
    $('#doctor-form').reset();
    $('#doctor-form [name="doctor_id"]').value = '';
    $('#form-title').textContent = 'Add doctor';
    $('#save-doctor').textContent = 'Add doctor';
    $('.method').textContent = 'POST';
    buildSchedule();
}

function loadSpecialities(selected = []) {
    request('/specialities/').then((specialities) => {
        $('#doctor-specialities').innerHTML = specialities.map((speciality) => `<option value="${speciality.id}" ${selected.includes(speciality.id) ? 'selected' : ''}>${speciality.speciality_name}</option>`).join('');
    }).catch((error) => showResult(error.message, false));
}

function editDoctor(doctor) {
    const form = $('#doctor-form');
    form.doctor_id.value = doctor.id;
    form.full_name.value = doctor.full_name;
    form.email.value = doctor.email;
    form.phone_number.value = doctor.phone_number;
    form.is_active.checked = doctor.is_active;
    [...form.specialities.options].forEach((option) => { option.selected = doctor.specialities.includes(Number(option.value)); });
    $('#form-title').textContent = `Edit ${doctor.full_name}`;
    $('#save-doctor').textContent = 'Save changes';
    $('.method').textContent = 'PATCH';
    buildSchedule(doctor.working_hours);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadDoctors() {
    try {
        const doctors = await request('/doctors/');
        $('#doctors-body').innerHTML = doctors.length ? doctors.map((doctor) => {
            const days = doctor.working_hours.map((item) => weekdays[item.weekday]).filter((day, index, list) => list.indexOf(day) === index).join(', ') || 'No schedule';
            return `<tr><td>${doctor.full_name}</td><td>${doctor.email}</td><td>${days}</td><td><button type="button" class="secondary edit-doctor" data-doctor-id="${doctor.id}">Edit</button></td></tr>`;
        }).join('') : '<tr><td colspan="4" class="empty">No doctors found.</td></tr>';
        document.querySelectorAll('.edit-doctor').forEach((button) => button.addEventListener('click', async () => {
            editDoctor(await request(`/doctors/${button.dataset.doctorId}/`));
        }));
    } catch (error) {
        $('#doctors-body').innerHTML = `<tr><td colspan="4" class="empty">${error.message}</td></tr>`;
    }
}

$('#doctor-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    if (!validateScheduleRows()) return;
    const data = {
        full_name: form.full_name.value,
        email: form.email.value,
        phone_number: form.phone_number.value,
        specialities: [...form.specialities.selectedOptions].map((option) => Number(option.value)),
        is_active: form.is_active.checked,
        working_hours: readSchedule(),
    };
    const doctorId = form.doctor_id.value;
    try {
        const result = await request(doctorId ? `/doctors/${doctorId}/` : '/doctors/', {
            method: doctorId ? 'PATCH' : 'POST', body: JSON.stringify(data),
        });
        showResult(result);
        await loadDoctors();
        resetForm();
    } catch (error) { showResult(error.message, false); }
});

document.addEventListener('change', (event) => {
    if (!event.target.matches('[data-weekday]')) return;
    const weekday = event.target.dataset.weekday;
    document.querySelector(`[data-start="${weekday}"]`).disabled = !event.target.checked;
    document.querySelector(`[data-end="${weekday}"]`).disabled = !event.target.checked;
});

$('#clear-form').addEventListener('click', resetForm);
$('#refresh-doctors').addEventListener('click', loadDoctors);
buildSchedule();
loadSpecialities();
loadDoctors();
