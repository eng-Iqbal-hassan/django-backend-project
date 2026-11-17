from django.core.validators import MinValueValidator
from django.db import models


class Kit(models.Model):
    """
    A kit in the shared stock. Stock is global (not per facility):
    any doctor, from any facility, can order any kit in stock.
    """

    name = models.CharField(max_length=255)
    variant_label = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    ice_packs_per_kit = models.PositiveIntegerField(default=0)
    fedex_packs_per_line = models.PositiveIntegerField(default=0)
    requisition_per_kit = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.variant_label})" if self.variant_label else self.name
