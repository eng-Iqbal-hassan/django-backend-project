from django.conf import settings
from django.db import models


class PickUp(models.Model):

    class Courier(models.TextChoices):
        FEDEX = "fedex", "FedEx"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SCHEDULED = "scheduled", "Scheduled"
        PICKED_UP = "picked_up", "Picked up"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    # The logged-in user who placed the pick-up.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pickups",
    )

    # Step 1
    has_fedex_pack = models.BooleanField(default=False)
    courier = models.CharField(
        max_length=20,
        choices=Courier.choices,
        default=Courier.FEDEX,
    )

    # Step 3
    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="pickups",
    )
    specimen_location = models.CharField(max_length=255)
    requested_by = models.CharField(max_length=255)
    needed_by = models.DateField()
    closing_time = models.TimeField()
    additional_notes = models.TextField(blank=True)

    # Shown as the "Pick up Timing Conflict" warning.
    has_timing_conflict = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # "Placed on"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pick up #{self.id}"
