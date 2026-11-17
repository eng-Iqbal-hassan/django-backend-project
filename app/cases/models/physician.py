from django.conf import settings
from django.db import models


class Physician(models.Model):
    """A doctor named on cases. Many physicians are not app users, so `user` is optional."""

    # e.g. "Sherif Nasr, MD"
    name = models.CharField(max_length=255)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="physician",
    )
    # The physician's ID in Tiger, used for syncing.
    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
