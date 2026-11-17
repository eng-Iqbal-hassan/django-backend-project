from django.core.validators import MinValueValidator
from django.db import models


class PickUpSample(models.Model):
    """How many of each sample type are in a pick-up (Step 2 chips and - / + stepper)."""

    pickup = models.ForeignKey(
        "pickups.PickUp",
        on_delete=models.CASCADE,
        related_name="samples",
    )
    sample_type = models.ForeignKey(
        "pickups.SampleType",
        on_delete=models.PROTECT,
        related_name="pickup_samples",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["pickup", "sample_type"], name="unique_pickup_sample_type"),
        ]

    def __str__(self):
        return f"{self.sample_type} x {self.quantity}"
