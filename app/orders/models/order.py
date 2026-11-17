from django.conf import settings
from django.db import models


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PREPARED = "prepared", "Prepared"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    # Step 1 of order creation: the facility this order is for.
    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    needed_by = models.DateField(null=True, blank=True)
    attention_to = models.CharField(max_length=255, blank=True)
    placed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        db_column="placed_by",
    )
    call_back_number = models.CharField(max_length=30, blank=True)
    additional_notes = models.TextField(blank=True)
    courier = models.CharField(max_length=100, blank=True)
    order_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    def __str__(self):
        return f"Order {self.id} - {self.order_status}"
