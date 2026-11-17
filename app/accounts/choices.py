from django.db import models


class Role(models.TextChoices):
    DOCTOR = "DOCTOR", "Doctor"
    SALESMAN = "SALESMAN", "Salesman"
