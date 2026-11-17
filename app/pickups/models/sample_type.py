from django.db import models


class SampleType(models.Model):
    """Lookup table for the sample-type chips in Step 2."""

    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
