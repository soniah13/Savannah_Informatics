from django.db import models

# Create your models here.
class Patient(models.Model):
    full_name = models.CharField(max_length=200)
    email=models.EmailField()
    phone_number=models.CharField(max_length=20)
    address=models.TextField()

    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name()









