from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    dependencies = [
        ('Savannah_app', '0007_alter_appointment_is_rescheduled'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='doctorworkinghours',
            constraint=models.CheckConstraint(
                condition=Q(('start_time__lt', F('end_time'))),
                name='working_hours_start_before_end',
            ),
        ),
    ]