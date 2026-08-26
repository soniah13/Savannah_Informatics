from django.db import migrations


def create_services(apps, schema_editor):
    Speciality = apps.get_model('Savannah_app', 'Speciality')
    ClinicalService = apps.get_model('Savannah_app', 'ClinicalService')

    for speciality in Speciality.objects.all():
        ClinicalService.objects.get_or_create(
            speciality_id=speciality.pk,
            defaults={
                'service_name': speciality.speciality_name,
                'service_description': speciality.speciality_description,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('Savannah_app', '0009_appointment_clinical_service'),
    ]

    operations = [
        migrations.RunPython(create_services, migrations.RunPython.noop),
    ]