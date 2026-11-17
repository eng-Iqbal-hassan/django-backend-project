from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class OrderItem(models.Model):
    """Which kits (and how many) are in order."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="items",
    )
    kit = models.ForeignKey(
        "orders.Kit",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "kit"], name="unique_order_kit"),
        ]

    def clean(self):
        if self.kit_id and self.quantity and self.quantity > self.kit.stock_quantity:
            raise ValidationError(
                {"quantity": f"Only {self.kit.stock_quantity} of '{self.kit}' in stock."}
            )

    def __str__(self):
        return f"{self.kit} x {self.quantity}"
