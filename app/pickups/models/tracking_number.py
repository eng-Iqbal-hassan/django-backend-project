from django.db import models
from django.utils import timezone


class TrackingNumber(models.Model):
    """A FedEx tracking number scanned in Step 1."""

    pickup = models.ForeignKey(
        "pickups.PickUp",
        on_delete=models.CASCADE,
        related_name="tracking_numbers",
    )
    number = models.CharField(max_length=100)
    scanned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["pickup", "number"], name="unique_pickup_tracking_number"),
        ]

    def __str__(self):
        return self.number
