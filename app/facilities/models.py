from django.conf import settings
from django.db import models


class Facility(models.Model):
    """A hospital facility (not a lab territory)."""

    facility_code = models.CharField(max_length=50, unique=True)
    facility_name = models.CharField(max_length=255)

    # A facility has many users; a user can be linked to many facilities.
    # Only doctors should be linked; that is checked where links are created.
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="facilities",
        blank=True,
    )

    def __str__(self):
        return f"{self.facility_code} - {self.facility_name}"
