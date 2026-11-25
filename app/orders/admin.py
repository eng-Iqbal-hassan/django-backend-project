from django.contrib import admin

from .models import Kit


@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ("name", "variant_label", "stock_quantity", "ice_packs_per_kit",
                    "fedex_packs_per_line", "requisition_per_kit")
    list_editable = ("stock_quantity",)
    search_fields = ("name", "variant_label")
    ordering = ("name", "variant_label")
