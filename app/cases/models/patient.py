from django.db import models


class Patient(models.Model):
    """
    A patient. No facility here: the same patient can belong to several
    facilities, so the facility is stored on each Case instead.
    """

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()

    class Meta:
        ordering = ["last_name", "first_name"]
        # Patient search uses name + DOB.
        indexes = [
            models.Index(fields=["last_name", "first_name", "date_of_birth"]),
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self):
        """'Greene, Melissa', as written on the request forms."""
        return f"{self.last_name}, {self.first_name}"

    def __str__(self):
        return self.full_name
